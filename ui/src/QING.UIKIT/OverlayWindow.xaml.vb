Imports System.Windows.Interop

Public Class OverlayWindow
    Private Const WS_EX_TOOLWINDOW As Integer = &H80
    Private Const WS_EX_NOACTIVATE As Integer = &H8000000
    Private Const GWL_EXSTYLE As Integer = -20

    <Runtime.InteropServices.DllImport("user32.dll")>
    Private Shared Function GetWindowLong(hwnd As IntPtr, index As Integer) As Integer
    End Function

    <Runtime.InteropServices.DllImport("user32.dll")>
    Private Shared Function SetWindowLong(hwnd As IntPtr, index As Integer, value As Integer) As Integer
    End Function

    Private Sub OverlayWindow_Loaded(sender As Object, e As RoutedEventArgs) Handles Me.Loaded
        Dim area = System.Windows.Forms.Screen.PrimaryScreen.WorkingArea
        Left = area.Right - Width - 24
        Top = area.Top + 24

        Dim hwnd = New WindowInteropHelper(Me).Handle
        Dim style = GetWindowLong(hwnd, GWL_EXSTYLE)
        SetWindowLong(hwnd, GWL_EXSTYLE, style Or WS_EX_TOOLWINDOW Or WS_EX_NOACTIVATE)

        AddHandler CoreBridge.LogReceived, AddressOf OnCoreLog
        AddHandler CoreBridge.StateChanged, AddressOf OnCoreStateChanged
        RefreshState()
    End Sub

    Private Sub OverlayWindow_Closed(sender As Object, e As EventArgs) Handles Me.Closed
        RemoveHandler CoreBridge.LogReceived, AddressOf OnCoreLog
        RemoveHandler CoreBridge.StateChanged, AddressOf OnCoreStateChanged
    End Sub

    Private Sub BtnOverlayStop_Click(sender As Object, e As MouseButtonEventArgs)
        CoreBridge.StopPipeline()
    End Sub

    Private Sub BtnOverlayHide_Click(sender As Object, e As MouseButtonEventArgs)
        Hide()
    End Sub

    Private Sub OnCoreLog(line As String)
        Dispatcher.Invoke(Sub()
                              LabOverlayLog.Text = line
                              RefreshState()
                          End Sub)
    End Sub

    Private Sub OnCoreStateChanged(isRunning As Boolean)
        Dispatcher.Invoke(AddressOf RefreshState)
    End Sub

    Private Sub RefreshState()
        LabOverlayState.Text = If(CoreBridge.IsRunning, "核心状态：运行中", "核心状态：空闲")
    End Sub

    Private Sub OverlayWindow_MouseLeftButtonDown(sender As Object, e As MouseButtonEventArgs) Handles Me.MouseLeftButtonDown
        If e.ButtonState = MouseButtonState.Pressed Then DragMove()
    End Sub
End Class
