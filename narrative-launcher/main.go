package main

import (
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"syscall"
	"time"
	"unsafe"

	"github.com/lxn/win"
)

const (
	backendPort  = 8000
	frontendPort = 5173
	llmPort      = 8080
	pollInterval = 3 * time.Second
)

// Service status tracking
type ServiceStatus struct {
	Name     string
	Port     int
	CheckURL string
	Healthy  bool
	ErrorMsg string
}

var (
	backendStatus  = &ServiceStatus{Name: "Backend", Port: backendPort, CheckURL: "/health/ready"}
	frontendStatus = &ServiceStatus{Name: "Frontend", Port: frontendPort, CheckURL: "/"}
	llmStatus      = &ServiceStatus{Name: "LLM", Port: llmPort, CheckURL: "/health/llm"}

	backendCmd  *exec.Cmd
	frontendCmd *exec.Cmd
	menu        win.HMENU
	statusMu    sync.Mutex
)

func main() {
	root := getRootDir()
	hInstance := win.GetModuleHandle(0)

	// Start services
	startBackend(root)
	go startFrontend(root)

	// Create tray
	menu = createMenu()
	hwnd := createMessageWindow(hInstance)
	registerTray(hwnd, hInstance)

	// Health polling
	go healthPoller(hwnd, hInstance)

	// Message loop
	runMessageLoop(hwnd)

	// Cleanup
	stopServices()
}

func getRootDir() string {
	execPath, _ := os.Executable()
	return filepath.Dir(execPath)
}

func startBackend(root string) {
	python := findPython(root)

	backendCmd = exec.Command(python, "-m", "uvicorn", "app.main:build_app", "--factory", "--host", "127.0.0.1", "--port", fmt.Sprintf("%d", backendPort))
	backendCmd.Dir = root
	backendCmd.Stdout = os.Stdout
	backendCmd.Stderr = os.Stderr
	backendCmd.SysProcAttr = &syscall.SysProcAttr{CreationFlags: win.CREATE_NO_WINDOW}

	if err := backendCmd.Start(); err != nil {
		log.Printf("Backend start failed: %v", err)
		return
	}

	for i := 0; i < 30; i++ {
		time.Sleep(1 * time.Second)
		if ping(fmt.Sprintf("http://127.0.0.1:%d/health/", backendPort)) == nil {
			log.Println("Backend ready")
			return
		}
	}
	log.Println("Backend startup timeout (may still be starting)")
}

func startFrontend(root string) {
	cwd := filepath.Join(root, "frontend")

	frontendCmd = exec.Command("npm", "run", "dev")
	frontendCmd.Dir = cwd
	frontendCmd.Stdout = os.Stdout
	frontendCmd.Stderr = os.Stderr
	frontendCmd.SysProcAttr = &syscall.SysProcAttr{CreationFlags: win.CREATE_NO_WINDOW}

	if err := frontendCmd.Start(); err != nil {
		log.Printf("Frontend start failed: %v", err)
		return
	}

	for i := 0; i < 20; i++ {
		time.Sleep(1 * time.Second)
		if ping(fmt.Sprintf("http://localhost:%d/", frontendPort)) == nil {
			log.Println("Frontend ready")
			return
		}
	}
	log.Println("Frontend startup timeout (may still be starting)")
}

func stopServices() {
	if backendCmd != nil && backendCmd.Process != nil {
		backendCmd.Process.Kill()
	}
	if frontendCmd != nil && frontendCmd.Process != nil {
		frontendCmd.Process.Kill()
	}
}

func findPython(root string) string {
	venv := filepath.Join(root, ".venv", "Scripts", "python.exe")
	if _, err := os.Stat(venv); err == nil {
		return venv
	}
	return "python"
}

func ping(url string) error {
	client := &http.Client{Timeout: 2 * time.Second}
	resp, err := client.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	io.Copy(io.Discard, resp.Body)
	if resp.StatusCode >= 500 {
		return fmt.Errorf("status %d", resp.StatusCode)
	}
	return nil
}

func createDotIcon(color win.DWORD, hInstance win.HINSTANCE) win.HICON {
	bm := win.CreateBitmap(16, 16, 1, 1, nil)
	dc := win.CreateCompatibleDC(0)
	oldBm := win.SelectObject(dc, bm)

	hBrush := win.CreateSolidBrush(color)
	oldBrush := win.SelectObject(dc, hBrush)
	win.Ellipse(dc, 2, 2, 14, 14)

	win.SelectObject(dc, oldBm)
	win.SelectObject(dc, oldBrush)
	win.DeleteObject(hBrush)
	win.DeleteDC(dc)

	var iconInfo win.ICONINFO
	iconInfo.fIcon = win.TRUE
	iconInfo.hbmMask = bm
	iconInfo.hbmColor = bm

	return win.CreateIconIndirect(&iconInfo)
}

func registerTray(hwnd win.HWND, hInstance win.HINSTANCE) {
	green := win.RGB(0, 255, 0)
	icon := createDotIcon(green, hInstance)

	var nid win.NOTIFYICONDATA
	nid.CBSize = uint32(unsafe.Sizeof(nid))
	nid.HWnd = hwnd
	nid.UID = 1
	nid.uFlags = win.NIF_ICON | win.NIF_MESSAGE | win.NIF_TIP
	nid.hIcon = icon
	nid.uCallbackMessage = win.WM_USER + 200
	copy(nid.szTip[:], syscall.StringToUTF16("Narrative Engine"))

	win.Shell_NotifyIcon(win.NIM_ADD, &nid)
}

func createMessageWindow(hInstance win.HINSTANCE) win.HWND {
	className := syscall.StringToUTF16Ptr("NarrativeLauncher")
	wc := win.WNDCLASSEX{}
	wc.CBSize = uint32(unsafe.Sizeof(wc))
	wc.hInstance = hInstance
	wc.lpfnWndProc = win.DefWindowProc
	wc.lpszClassName = className

	win.RegisterClassEx(&wc)
	return win.CreateWindowEx(0, className, nil, 0, 0, 0, 0, 0, 0, 0, hInstance, nil)
}

func createMenu() win.HMENU {
	m := win.CreatePopupMenu()
	win.AppendMenu(m, win.MF_STRING, 1001, "Open Frontend")
	win.AppendMenu(m, win.MF_STRING, 1002, "Open API Docs")
	win.AppendMenu(win.MF_SEPARATOR, 0, nil)
	win.AppendMenu(m, win.MF_STRING, 1003, "View Logs")
	win.AppendMenu(win.MF_SEPARATOR, 0, nil)
	win.AppendMenu(m, win.MF_STRING, 1004, "Exit")
	return m
}

func checkServices() {
	statusMu.Lock()
	defer statusMu.Unlock()

	if err := ping(fmt.Sprintf("http://127.0.0.1:%d%s", backendStatus.Port, backendStatus.CheckURL)); err == nil {
		backendStatus.Healthy = true
		backendStatus.ErrorMsg = ""
	} else {
		backendStatus.Healthy = false
		backendStatus.ErrorMsg = err.Error()
	}

	if err := ping(fmt.Sprintf("http://127.0.0.1:%d%s", llmStatus.Port, llmStatus.CheckURL)); err == nil {
		llmStatus.Healthy = true
		llmStatus.ErrorMsg = ""
	} else {
		llmStatus.Healthy = false
		llmStatus.ErrorMsg = err.Error()
	}

	if err := ping(fmt.Sprintf("http://localhost:%d%s", frontendStatus.Port, frontendStatus.CheckURL)); err == nil {
		frontendStatus.Healthy = true
		frontendStatus.ErrorMsg = ""
	} else {
		frontendStatus.Healthy = false
		frontendStatus.ErrorMsg = err.Error()
	}
}

func updateTrayIcon(hwnd win.HWND, hInstance win.HINSTANCE) {
	statusMu.Lock()
	allHealthy := backendStatus.Healthy && frontendStatus.Healthy && llmStatus.Healthy
	statusMu.Unlock()

	var color win.DWORD
	if allHealthy {
		color = win.RGB(0, 255, 0)
	} else {
		color = win.RGB(255, 140, 0)
	}

	newIcon := createDotIcon(color, hInstance)

	var nid win.NOTIFYICONDATA
	nid.CBSize = uint32(unsafe.Sizeof(nid))
	nid.HWnd = hwnd
	nid.UID = 1
	nid.uFlags = win.NIF_ICON
	nid.hIcon = newIcon
	win.Shell_NotifyIcon(win.NIM_MODIFY, &nid)
}

func healthPoller(hwnd win.HWND, hInstance win.HINSTANCE) {
	ticker := time.NewTicker(pollInterval)
	defer ticker.Stop()

	for range ticker.C {
		checkServices()
		updateTrayIcon(hwnd, hInstance)
	}
}

func openURL(url string) {
	exec.Command("cmd", "/c", "start", url).Start()
}

func handleMenuCommand(cmdID uint32) {
	switch cmdID {
	case 1001:
		openURL("http://localhost:5173")
	case 1002:
		openURL("http://127.0.0.1:8000/docs")
	case 1003:
		openURL("file:///C:/Users/SLuh/AppData/Local/Temp/opencode/bg-out.log")
	case 1004:
		stopServices()
		os.Exit(0)
	}
}

func handleTrayMessage(msg win.MSG, hwnd win.HWND) {
	x := int(win.LOWORD(msg.LParam))
	y := int(win.HIWORD(msg.LParam))

	if msg.WParam == win.WM_RBUTTONUP {
		statusMu.Lock()
		allHealthy := backendStatus.Healthy && frontendStatus.Healthy && llmStatus.Healthy
		statusMu.Unlock()

		// Rebuild menu with current status
		win.DestroyMenu(menu)
		menu = win.CreatePopupMenu()

		win.AppendMenu(menu, win.MF_STRING, 1001, "Open Frontend (http://localhost:5173)")
		win.AppendMenu(menu, win.MF_STRING, 1002, "Open API Docs (http://127.0.0.1:8000/docs)")

		if allHealthy {
			win.AppendMenu(menu, win.MF_STRING, 1005, "Status: All services healthy")
		} else {
			var issues []string
			if !backendStatus.Healthy {
				issues = append(issues, "Backend")
			}
			if !frontendStatus.Healthy {
				issues = append(issues, "Frontend")
			}
			if !llmStatus.Healthy {
				issues = append(issues, "LLM")
			}
			win.AppendMenu(menu, win.MF_STRING, 1005, fmt.Sprintf("Status: %s unhealthy", strings.Join(issues, ", ")))
		}

		win.AppendMenu(win.MF_SEPARATOR, 0, nil)
		win.AppendMenu(menu, win.MF_STRING, 1003, "View Logs")
		win.AppendMenu(win.MF_SEPARATOR, 0, nil)
		win.AppendMenu(menu, win.MF_STRING, 1004, "Exit")

		win.SetForegroundWindow(hwnd)
		win.TrackPopupMenu(menu, win.TPM_RIGHTBUTTON|win.TPM_CENTERALIGN, x, y, 0, hwnd, nil)
	}
}

func runMessageLoop(hwnd win.HWND) {
	var msg win.MSG
	for {
		if win.GetMessage(&msg, 0, 0, 0) == win.FALSE {
			break
		}
		win.TranslateMessage(&msg)
		win.DispatchMessage(&msg)

		if msg.Message == win.WM_USER+200 {
			switch uint32(msg.LParam) {
			case win.WM_RBUTTONUP:
				handleTrayMessage(msg, hwnd)
			case win.WM_LBUTTONDOWN:
				openURL("http://localhost:5173")
			}
		}
	}
}
