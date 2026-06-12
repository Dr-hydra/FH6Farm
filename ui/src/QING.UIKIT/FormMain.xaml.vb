Imports System.Windows.Interop

Public Class FormMain
    Private Const WM_HOTKEY As Integer = &H312
    Private Const HotkeyStartId As Integer = &H5101
    Private Const HotkeyStopId As Integer = &H5102
    Private Const ModAlt As UInteger = &H1
    Private Const ModControl As UInteger = &H2
    Private Const ModShift As UInteger = &H4
    Private Const ModWin As UInteger = &H8
    Private Const ModNoRepeat As UInteger = &H4000

    <Runtime.InteropServices.DllImport("user32.dll")>
    Private Shared Function RegisterHotKey(hwnd As IntPtr, id As Integer, modifiers As UInteger, virtualKey As UInteger) As Boolean
    End Function

    <Runtime.InteropServices.DllImport("user32.dll")>
    Private Shared Function UnregisterHotKey(hwnd As IntPtr, id As Integer) As Boolean
    End Function

    Private ReadOnly PageHost As New UiKitShellHost()
    Private PageOverview As PageUiKitRight
    Private PageControls As PageUiKitRight
    Private PageLayout As PageUiKitRight
    Private PageTheme As PageUiKitRight
    Private PageAbout As PageUiKitRight
    Private IsSizeSaveable As Boolean = False
    Private HotkeySource As HwndSource
    Private TaskOverlay As OverlayWindow

    Public PageRight As MyPageRight
    Public Property Hidden As Boolean

    Public Sub New()
        ApplicationStartTick = GetTimeMs()
        FrmMain = Me
        ThemeCheckAll(False)
        ThemeRefresh(Settings.Get(Of Integer)("UiLauncherTheme"))

        PageOverview = PageUiKitRight.Create(UiKitDemoPage.Overview)
        PageControls = PageUiKitRight.Create(UiKitDemoPage.Controls)
        PageLayout = PageUiKitRight.Create(UiKitDemoPage.Layout)
        PageTheme = PageUiKitRight.Create(UiKitDemoPage.Theme)
        PageAbout = PageUiKitRight.Create(UiKitDemoPage.About)

        InitializeComponent()
        Opacity = 0

        PanMainRight.Child = PageOverview
        PageRight = PageOverview
        PageHost.CurrentPage = UiKitDemoPage.Overview
        PageOverview.PageState = MyPageRight.PageStates.ContentStay
    End Sub

    Private Sub FormMain_Loaded(sender As Object, e As RoutedEventArgs) Handles Me.Loaded
        Handle = New WindowInteropHelper(Me).Handle
        HotkeySource = HwndSource.FromHwnd(Handle)
        HotkeySource.AddHook(AddressOf WindowProc)
        UpdateBackgroundAndTitleBar()
        BtnExtraBack.ShowCheck = AddressOf BtnExtraBack_ShowCheck

        Dim Resizer As New MyResizer(Me)
        Resizer.addResizerDown(ResizerB)
        Resizer.addResizerLeft(ResizerL)
        Resizer.addResizerLeftDown(ResizerLB)
        Resizer.addResizerLeftUp(ResizerLT)
        Resizer.addResizerRight(ResizerR)
        Resizer.addResizerRightDown(ResizerRB)
        Resizer.addResizerRightUp(ResizerRT)
        Resizer.addResizerUp(ResizerT)

        ThemeRefreshMain()
        BtnTitleSelect0.SetChecked(True, False, False)
        Height = Math.Max(Settings.Get(Of Integer)("WindowHeight"), MinHeight)
        Width = Math.Max(Settings.Get(Of Integer)("WindowWidth"), MinWidth)
        Top = (GetWPFSize(System.Windows.Forms.Screen.PrimaryScreen.WorkingArea.Height) - Height) / 2
        Left = (GetWPFSize(System.Windows.Forms.Screen.PrimaryScreen.WorkingArea.Width) - Width) / 2
        IsSizeSaveable = True
        ShowWindowToTop()
        RefreshGlobalHotkeys(CoreBridge.LoadConfig())
        ShowTaskOverlay()

        AniStart({
            AaCode(Sub() AniControlEnabled = 0, 50),
            AaOpacity(Me, Settings.Get(Of Integer)("UiLauncherTransparent") / 1000 + 0.4, 250, 100),
            AaDouble(Sub(i) TransformPos.Y += i, -TransformPos.Y, 600, 100, New AniEaseOutBack(AniEasePower.Weak)),
            AaDouble(Sub(i) TransformRotate.Angle += i, -TransformRotate.Angle, 500, 100, New AniEaseOutBack(AniEasePower.Weak)),
            AaCode(Sub()
                       PanBack.RenderTransform = Nothing
                       Logger.Info("FH6Auto UI started.")
                   End Sub, , True)
        }, "Form Show")

        Hint("FH6Auto UI 已加载。", HintType.Green)
    End Sub

    Public Shared Sub UpdateBackgroundAndTitleBar(value)
        If FrmMain Is Nothing OrElse Not FrmMain.IsLoaded Then Return
        FrmMain.UpdateBackgroundAndTitleBar()
    End Sub

    Public Sub UpdateBackgroundAndTitleBar()
        ShapeTitleLogo.Visibility = Visibility.Collapsed
        LabTitleLogo.Visibility = Visibility.Visible
        ImageTitleLogo.Visibility = Visibility.Collapsed
        PanTitleSelect.Visibility = Visibility.Visible
        LabTitleLogo.Text = "FH6Auto"
        PanTitleMain.ColumnDefinitions(0).Width = New GridLength(1, GridUnitType.Star)
    End Sub

    Private Sub BtnTitleClose_Click(sender As Object, e As EventArgs) Handles BtnTitleClose.Click
        SaveActivePageConfig()
        ReleaseGlobalHotkeys()
        If TaskOverlay IsNot Nothing Then TaskOverlay.Close()
        Close()
    End Sub

    Private Sub FormMain_Closing(sender As Object, e As ComponentModel.CancelEventArgs) Handles Me.Closing
        SaveActivePageConfig()
    End Sub

    Public Sub StartConfiguredTask()
        Dim config = SaveActivePageConfig()
        CoreBridge.StartTask(config.HotkeyStartTask)
    End Sub

    Public Sub StopCurrentTask()
        CoreBridge.StopTask()
    End Sub

    Public Sub ShowTaskOverlay()
        If TaskOverlay Is Nothing OrElse Not TaskOverlay.IsLoaded Then TaskOverlay = New OverlayWindow()
        TaskOverlay.Show()
    End Sub

    Public Sub HideTaskOverlay()
        If TaskOverlay IsNot Nothing Then TaskOverlay.HideOverlay()
    End Sub

    Public Sub RefreshGlobalHotkeys(config As FH6AutoConfig)
        ReleaseGlobalHotkeys()
        If Handle = IntPtr.Zero Then Return

        RegisterConfiguredHotkey(HotkeyStartId, config.StartHotkey, "开始")
        RegisterConfiguredHotkey(HotkeyStopId, config.StopHotkey, "停止")
        If TaskOverlay IsNot Nothing Then TaskOverlay.RefreshState()
    End Sub

    Public Sub NotifyConfigSaved(config As FH6AutoConfig)
        RefreshGlobalHotkeys(config)
        PageOverview.ReloadConfig()
        PageControls.ReloadConfig()
        PageLayout.ReloadConfig()
        PageTheme.ReloadConfig()
        PageAbout.ReloadConfig()
    End Sub

    Private Function SaveActivePageConfig() As FH6AutoConfig
        Dim activePage = TryCast(PanMainRight.Child, PageUiKitRight)
        If activePage IsNot Nothing Then
            Try
                Return activePage.SaveVisibleConfig()
            Catch ex As Exception
                CoreBridge.PublishLog("保存当前页面配置失败：" & ex.Message)
            End Try
        End If

        Return CoreBridge.LoadConfig()
    End Function

    Private Sub RegisterConfiguredHotkey(id As Integer, text As String, actionName As String)
        Dim modifiers As UInteger
        Dim virtualKey As UInteger
        If Not TryParseHotkey(text, modifiers, virtualKey) Then
            CoreBridge.PublishLog($"{actionName}快捷键无效：{text}")
            Return
        End If
        If Not RegisterHotKey(Handle, id, modifiers Or ModNoRepeat, virtualKey) Then
            CoreBridge.PublishLog($"{actionName}快捷键注册失败，可能已被其他程序占用：{text}")
        End If
    End Sub

    Private Sub ReleaseGlobalHotkeys()
        If Handle = IntPtr.Zero Then Return
        UnregisterHotKey(Handle, HotkeyStartId)
        UnregisterHotKey(Handle, HotkeyStopId)
    End Sub

    Private Function TryParseHotkey(text As String, ByRef modifiers As UInteger, ByRef virtualKey As UInteger) As Boolean
        modifiers = 0
        virtualKey = 0
        For Each rawPart In If(text, "").Split("+"c)
            Dim part = rawPart.Trim().ToUpperInvariant()
            Select Case part
                Case "CTRL", "CONTROL"
                    modifiers = modifiers Or ModControl
                Case "ALT"
                    modifiers = modifiers Or ModAlt
                Case "SHIFT"
                    modifiers = modifiers Or ModShift
                Case "WIN", "WINDOWS"
                    modifiers = modifiers Or ModWin
                Case ""
                    Return False
                Case Else
                    Try
                        Dim key = CType(New KeyConverter().ConvertFromString(part), Key)
                        virtualKey = CUInt(KeyInterop.VirtualKeyFromKey(key))
                    Catch
                        Return False
                    End Try
            End Select
        Next
        Return virtualKey <> 0
    End Function

    Private Function WindowProc(hwnd As IntPtr, message As Integer, wParam As IntPtr, lParam As IntPtr, ByRef handled As Boolean) As IntPtr
        If message <> WM_HOTKEY Then Return IntPtr.Zero
        Select Case wParam.ToInt32()
            Case HotkeyStartId
                StartConfiguredTask()
            Case HotkeyStopId
                StopCurrentTask()
        End Select
        handled = True
        Return IntPtr.Zero
    End Function

    Private Sub BtnTitleMin_Click(sender As Object, e As EventArgs) Handles BtnTitleMin.Click
        WindowState = WindowState.Minimized
    End Sub

    Private Sub FormDragMove(sender As Object, e As MouseButtonEventArgs) Handles PanTitle.MouseLeftButtonDown, PanMsg.MouseLeftButtonDown
        If e.ClickCount >= 2 Then
            WindowState = If(WindowState = WindowState.Maximized, WindowState.Normal, WindowState.Maximized)
        ElseIf sender.IsMouseDirectlyOver Then
            DragMove()
        End If
    End Sub

    Private Sub FormMain_DragEnter(sender As Object, e As DragEventArgs) Handles Me.DragEnter, Me.DragOver
        e.Handled = True
        e.Effects = If(UiKitFileDropService.HasFileDrop(e), DragDropEffects.Copy, DragDropEffects.None)
    End Sub

    Private Sub FormMain_Drop(sender As Object, e As DragEventArgs) Handles Me.Drop
        Dim files = UiKitFileDropService.GetDroppedFiles(e)
        If files.Count = 0 Then Return
        Hint($"已接收 {files.Count} 个拖放文件。")
        PageOverview.ShowDroppedFiles(files)
    End Sub

    Private Sub FormMain_SizeChanged() Handles Me.SizeChanged, Me.Loaded
        If IsSizeSaveable Then
            Settings.Set("WindowHeight", CInt(Height))
            Settings.Set("WindowWidth", CInt(Width))
        End If
        RectForm.Rect = New Rect(0, 0, BorderForm.ActualWidth, BorderForm.ActualHeight)
        PanForm.Width = BorderForm.ActualWidth + 0.001
        PanForm.Height = BorderForm.ActualHeight + 0.001
        PanMain.Width = PanForm.Width
        PanMain.Height = Math.Max(0, PanForm.Height - PanTitle.ActualHeight)
        If WindowState = WindowState.Maximized Then WindowState = WindowState.Normal
    End Sub

    Private Sub BtnTitleSelect_Click(sender As MyRadioButton, raiseByMouse As Boolean) Handles BtnTitleSelect0.Check, BtnTitleSelect1.Check, BtnTitleSelect2.Check, BtnTitleSelect3.Check, BtnTitleSelect4.Check
        PageChange(CType(Val(sender.Tag), UiKitDemoPage))
    End Sub

    Public Sub PageChange(page As UiKitDemoPage)
        If PageHost.CurrentPage = page Then Return
        SaveActivePageConfig()
        PageHost.LastPage = PageHost.CurrentPage
        PageHost.CurrentPage = page

        Dim target = GetRightPage(page)
        target.ReloadConfig()
        PageRight = target
        PageChangeAnim(target)
        Hint("已切换到：" & UiKitShellText.GetPageTitle(page))
    End Sub

    Private Function GetRightPage(page As UiKitDemoPage) As PageUiKitRight
        Select Case page
            Case UiKitDemoPage.Controls
                Return PageControls
            Case UiKitDemoPage.Layout
                Return PageLayout
            Case UiKitDemoPage.Theme
                Return PageTheme
            Case UiKitDemoPage.About
                Return PageAbout
            Case Else
                Return PageOverview
        End Select
    End Function

    Private Sub PageChangeAnim(target As MyPageRight)
        If target Is Nothing Then Return
        AniStop("FrmMain PageChangeRight")
        AniControlEnabled += 1
        If PanMainRight.Child IsNot Nothing AndAlso TypeOf PanMainRight.Child Is MyPageRight Then
            CType(PanMainRight.Child, MyPageRight).PageOnExit()
        End If
        AniControlEnabled -= 1
        AniStart({
            AaCode(Sub()
                       AniControlEnabled += 1
                       If PanMainRight.Child IsNot Nothing AndAlso TypeOf PanMainRight.Child Is MyPageRight Then
                           CType(PanMainRight.Child, MyPageRight).PageOnForceExit()
                       End If
                       PanMainRight.Child = target
                       target.Opacity = 0
                       AniControlEnabled -= 1
                       BtnExtraBack.ShowRefresh()
                   End Sub, 110),
            AaCode(Sub()
                       target.Opacity = 1
                       target.PageOnEnter()
                   End Sub, 30, True)
        }, "FrmMain PageChangeRight")
    End Sub

    Public Sub ShowWindowToTop()
        Visibility = Visibility.Visible
        ShowInTaskbar = True
        WindowState = WindowState.Normal
        Topmost = True
        Topmost = False
        Activate()
        Focus()
    End Sub

    Public Sub BackToTop() Handles BtnExtraBack.Click
        Dim scroll = UiKitShellNavigation.GetActiveScroll(PanMainRight.Child)
        If scroll IsNot Nothing Then scroll.PerformVerticalOffsetDelta(-scroll.VerticalOffset)
    End Sub

    Private Function BtnExtraBack_ShowCheck() As Boolean
        Dim scroll = UiKitShellNavigation.GetActiveScroll(PanMainRight.Child)
        Return scroll IsNot Nothing AndAlso scroll.Visibility = Visibility.Visible AndAlso scroll.VerticalOffset > Height + If(BtnExtraBack.Show, 0, 700)
    End Function

    Public Sub DragDoing()
    End Sub

    Public Sub DragStop()
    End Sub

    Public Sub DragTick()
    End Sub

    Public Sub SliderDrag_Finish()
    End Sub

    Public Shared Sub EndProgramForce(returnValue As ProcessReturnValues)
        Environment.Exit(CInt(returnValue))
    End Sub

End Class
