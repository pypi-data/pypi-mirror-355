pragma Singleton
import QtQuick 2.15

Item {
    function _isWinMgrInitialized() {
        return typeof WinEventManager!== "undefined"
    }

    function sendDragWindowEvent(window) {
        if (!_isWinMgrInitialized()) {
            console.error("ThemeManager is not defined.")
            return -1
        }
        WinEventManager.dragWindowEvent(WinEventManager.getWindowId(window))
    }

    function maximizeWindow(window) {
        if (!_isWinMgrInitialized()) {
            console.error("ThemeManager is not defined.")
            return -1
        }
        if ((Qt.platform.os !== "windows" || Qt.platform.os !== "winrt") && _isWinMgrInitialized()) {
            WinEventManager.maximizeWindow(WinEventManager.getWindowId(window))
            return  // 在win环境使用原生方法拖拽
        }

        window.showMaximized()
    }
}