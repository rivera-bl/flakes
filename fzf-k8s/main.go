package main

import (
	"bytes"
	"fmt"
	"context" // Required for client-go operations
	"io"
	"log"
	"os"
	"os/exec"
	"strings"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"
	// Uncomment the following line if running inside a cluster
	// "k8s.io/client-go/rest"
)

func main() {
	// 1. Setup Kubernetes client
	// Get kubeconfig path from environment variable KUBECONFIG
	kubeconfigPath := os.Getenv("KUBECONFIG")
	// If KUBECONFIG is not set, kubeconfigPath will be "",
	// and BuildConfigFromFlags will use default loading rules (~/.kube/config)

	// Build configuration using the explicit path from KUBECONFIG env var,
	// or default rules if KUBECONFIG is not set.
	config, err := clientcmd.BuildConfigFromFlags("", kubeconfigPath) // "" for masterUrl, kubeconfigPath from env or ""
	if err != nil {
		// Fallback: try in-cluster config if loading fails
		// log.Printf("Could not load kubeconfig from path '%s': %v. Trying in-cluster config.", kubeconfigPath, err)
		// config, err = rest.InClusterConfig()
		// if err != nil {
		log.Fatalf("Failed to configure Kubernetes client: %v", err)
		// }
	}

	// Create the clientset
	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		log.Fatalf("Failed to create Kubernetes clientset: %v", err)
	}

	// 2. List pods using the client
	pods, err := clientset.CoreV1().Pods("").List(context.TODO(), metav1.ListOptions{})
	if err != nil {
		log.Fatalf("Failed to list pods: %v", err)
	}

	if len(pods.Items) == 0 {
		log.Fatalf("No pods found in the cluster.")
	}

	// 3. Format pod list for fzf
	var podListBuffer bytes.Buffer
	for _, pod := range pods.Items {
		// Format: NAMESPACE NAME
		_, err := fmt.Fprintf(&podListBuffer, "%s %s\n", pod.Namespace, pod.Name)
		if err != nil {
			log.Fatalf("Failed to write pod info to buffer: %v", err)
		}
	}
	podListBytes := podListBuffer.Bytes() // Use bytes directly

	// 4. Setup fzf command
	fzfCmd := exec.Command("fzf")

	// Get pipes for stdin and stdout
	fzfInPipe, err := fzfCmd.StdinPipe()
	if err != nil {
		log.Fatalf("Failed to get stdin pipe for fzf: %v", err)
	}
	fzfOutPipe, err := fzfCmd.StdoutPipe()
	if err != nil {
		log.Fatalf("Failed to get stdout pipe for fzf: %v", err)
	}

	// Set stderr to os.Stderr to show fzf UI errors and allow interaction
	fzfCmd.Stderr = os.Stderr

	// Start fzf
	err = fzfCmd.Start()
	if err != nil {
		log.Fatalf("Failed to start fzf command: %v", err)
	}

	// Write kubectl output to fzf's stdin in a goroutine
	go func() {
		defer fzfInPipe.Close()
		_, err := fzfInPipe.Write(podListBytes)
		if err != nil {
			// Log error, but don't necessarily kill the main process,
			// fzf might still run or exit cleanly.
			log.Printf("Error writing to fzf stdin pipe: %v", err)
		}
	}()

	// Read fzf's selected output from its stdout pipe
	var fzfOutput bytes.Buffer
	_, err = io.Copy(&fzfOutput, fzfOutPipe) // Use io.Copy
	if err != nil {
		log.Fatalf("Failed to read fzf output pipe: %v", err)
	}

	// Wait for fzf to finish
	err = fzfCmd.Wait()
	if err != nil {
		// Check if fzf was cancelled (exit code 130) or if no selection was made (exit code 1)
		if exitErr, ok := err.(*exec.ExitError); ok {
			// Exit code 1 means no match, 130 means cancelled (e.g., Ctrl+C, Esc)
			if exitErr.ExitCode() == 1 || exitErr.ExitCode() == 130 {
				fmt.Println("No pod selected.")
				os.Exit(0) // Exit gracefully
			}
		}
		// Log other fzf errors
		log.Fatalf("fzf command failed with error: %v", err)
	}

	// Process the selection
	selectedPod := strings.TrimSpace(fzfOutput.String())

	if selectedPod == "" {
		// This case might be redundant due to the exit code check above, but good for safety.
		fmt.Println("No pod selected.")
	} else {
		// Parse the selected line: "namespace podname"
		parts := strings.Fields(selectedPod)
		if len(parts) != 2 {
			log.Fatalf("Error: Invalid format returned from fzf: %q", selectedPod)
		}
		namespace := parts[0]
		podName := parts[1]

		// Check if running inside tmux
		if os.Getenv("TMUX") == "" {
			log.Fatalf("Error: Not running inside a tmux session. Cannot use send-keys.")
		}

		// fmt.Printf("Sending 'kubectl logs -f %s -n %s' to current tmux pane...\n", podName, namespace)

		// Construct the kubectl command string
		kubectlCmdStr := fmt.Sprintf("kubectl logs -f %s -n %s", podName, namespace)

		// Execute tmux send-keys
		// Omitting -t sends to the current pane by default
		// C-m sends the Enter key
		tmuxCmd := exec.Command("tmux", "send-keys", "-t", "bottom-right", kubectlCmdStr, "C-m")
		tmuxCmd.Stdout = os.Stdout // Show tmux command output (if any)
		tmuxCmd.Stderr = os.Stderr // Show tmux command errors

		err = tmuxCmd.Run() // Run the command and wait for it to complete
		if err != nil {
			log.Fatalf("Failed to execute tmux send-keys: %v", err)
		}
		// fmt.Println("Command sent to tmux.")
	}
}
