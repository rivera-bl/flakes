package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"path/filepath"

	fuzzyfinder "github.com/ktr0731/go-fuzzyfinder"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"time" // Import the time package for timeout

	// Note: Duplicate imports removed below
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"
	// Recommended for GCP/Azure/etc authentication
	// _ "k8s.io/client-go/plugin/pkg/client/auth"
)

// PodInfo holds basic information about a Kubernetes pod
type PodInfo struct {
	Namespace string
	Name      string
}

// String returns a string representation for display in the fuzzy finder
func (p PodInfo) String() string {
	return fmt.Sprintf("%s/%s", p.Namespace, p.Name)
}

func main() {
	// --- Kubernetes Client Setup ---
	kubeconfig := os.Getenv("KUBECONFIG")
	if kubeconfig == "" {
		home, err := os.UserHomeDir()
		if err != nil {
			log.Fatalf("Error getting user home directory: %v\n", err)
		}
		kubeconfig = filepath.Join(home, ".kube", "config")
	}

	config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		log.Fatalf("Error building kubeconfig: %v\n", err)
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		log.Fatalf("Error creating Kubernetes client: %v\n", err)
	}

	// --- List Pods ---
	log.Println("Attempting to fetch pods from all namespaces...") // Added log
	// Create a context with a timeout (e.g., 30 seconds)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel() // Ensure the context is cancelled to release resources

	pods, err := clientset.CoreV1().Pods("").List(ctx, v1.ListOptions{})
	if err != nil {
		log.Fatalf("Error listing pods: %v\n", err) // This will now trigger on timeout as well
	}
	log.Println("Successfully fetched pods.") // Added log

	if len(pods.Items) == 0 {
		fmt.Println("No pods found in any namespace.")
		return
	}

	// --- Prepare Data for Fuzzy Finder ---
	podInfos := make([]PodInfo, len(pods.Items))
	for i, pod := range pods.Items {
		podInfos[i] = PodInfo{
			Namespace: pod.Namespace,
			Name:      pod.Name,
		}
	}
	log.Println("Preparing data for fuzzy finder...") // Added log

	// --- Run Fuzzy Finder ---
	log.Println("Starting fuzzy finder...") // Added log
	idx, err := fuzzyfinder.Find(
		podInfos,
		func(i int) string {
			// Use the String() method we defined for PodInfo
			return podInfos[i].String()
		},
		fuzzyfinder.WithHeader("Select a Pod (Namespace/Name):"),
	)

	// Handle potential errors (e.g., user pressing Esc)
	if err != nil {
		if err == fuzzyfinder.ErrAbort {
			fmt.Println("No pod selected.")
			os.Exit(0)
		}
		log.Fatalf("Error running fuzzy finder: %v\n", err)
	}

	// --- Display Selection ---
	selectedPod := podInfos[idx]
	fmt.Printf("You selected: %s/%s\n", selectedPod.Namespace, selectedPod.Name)
}
