Imports System.Windows.Interop

Public Class OverlayWindow
    Private Const WS_EX_TOOLWINDOW As Integer = &H80
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
        SetWindowLong(hwnd, GWL_EXSTYLE, style Or WS_EX_TOOLWINDOW)

        AddHandler CoreBridge.LogReceived, AddressOf OnCoreLog
        AddHandler CoreBridge.StateChanged, AddressOf OnCoreStateChanged
        RefreshState()
    End Sub

    Private Sub OverlayWindow_Closed(sender As Object, e As EventArgs) Handles Me.Closed
        RemoveHandler CoreBridge.LogReceived, AddressOf OnCoreLog
        RemoveHandler CoreBridge.StateChanged, AddressOf OnCoreStateChanged
    End Sub

    Private Sub BtnOverlayStop_Click(sender As Object, e As MouseButtonEventArgs)
        FrmMain?.StopCurrentTask()
    End Sub

    Private Sub BtnOverlayStart_Click(sender As Object, e As MouseButtonEventArgs)
        FrmMain?.StartConfiguredTask()
    End Sub

    Private Sub BtnOverlayHide_Click(sender As Object, e As MouseButtonEventArgs)
        HideOverlay()
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

    Public Sub RefreshState()
        LabOverlayState.Text = If(CoreBridge.IsRunning, "任务状态：运行中", "任务状态：空闲")
        Dim config = CoreBridge.LoadConfig()
        LabOverlayHotkeys.Text = $"开始：{config.StartHotkey}（{TaskName(config.HotkeyStartTask)}）  |  停止：{config.StopHotkey}"
    End Sub

    Public Sub HideOverlay()
        Dispatcher.BeginInvoke(Sub() Hide())
    End Sub

    Private Function TaskName(task As String) As String
        Select Case task
            Case "buy"
                Return "买车"
            Case "cj"
                Return "抽奖"
            Case "sell"
                Return "移除"
            Case Else
                Return "跑图"
        End Select
    End Function

    Private Sub OverlayWindow_MouseLeftButtonDown(sender As Object, e As MouseButtonEventArgs) Handles Me.MouseLeftButtonDown
        Dim source = TryCast(e.OriginalSource, DependencyObject)
        While source IsNot Nothing
            If TypeOf source Is MyButton Then Return
            source = Media.VisualTreeHelper.GetParent(source)
        End While
        If e.ButtonState = MouseButtonState.Pressed Then DragMove()
    End Sub
End Class
