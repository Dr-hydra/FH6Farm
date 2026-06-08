Public Class PageUiKitRight
    Private Page As UiKitDemoPage = UiKitDemoPage.Overview
    Private CurrentConfig As FH6AutoConfig
    Private Overlay As OverlayWindow

    Public ReadOnly Property Subtitle As String
        Get
            Return LabSubtitle.Text
        End Get
    End Property

    Public Shared Function Create(page As UiKitDemoPage) As PageUiKitRight
        Dim result As New PageUiKitRight()
        result.Configure(page)
        Return result
    End Function

    Public Sub Configure(page As UiKitDemoPage)
        Me.Page = page
        LabTitle.Text = UiKitShellText.GetPageTitle(page)

        CardDashboard.Visibility = If(page = UiKitDemoPage.Overview, Visibility.Visible, Visibility.Collapsed)
        CardFlow.Visibility = If(page = UiKitDemoPage.Controls, Visibility.Visible, Visibility.Collapsed)
        CardOverlay.Visibility = If(page = UiKitDemoPage.Layout, Visibility.Visible, Visibility.Collapsed)
        CardSettings.Visibility = If(page = UiKitDemoPage.Theme, Visibility.Visible, Visibility.Collapsed)
        CardAbout.Visibility = If(page = UiKitDemoPage.About, Visibility.Visible, Visibility.Collapsed)

        Select Case page
            Case UiKitDemoPage.Controls
                LabSubtitle.Text = "配置四个自动化模块的次数、串联顺序和技能路径。"
            Case UiKitDemoPage.Layout
                LabSubtitle.Text = "运行时置顶小窗，用于在游戏前方查看状态和停止核心。"
            Case UiKitDemoPage.Theme
                LabSubtitle.Text = "自动重启、移除模式、计算器参数和配置文件路径。"
            Case UiKitDemoPage.About
                LabSubtitle.Text = "来源、作者、UI 重制边界和当前架构说明。"
            Case Else
                LabSubtitle.Text = "快速启动 Python 自动化核心，并查看实时日志。"
        End Select

        RefreshStateLabel()
    End Sub

    Private Sub PageUiKitRight_Loaded(sender As Object, e As RoutedEventArgs) Handles Me.Loaded
        AddHandler CoreBridge.LogReceived, AddressOf OnCoreLog
        AddHandler CoreBridge.StateChanged, AddressOf OnCoreStateChanged
        LoadState.State.LoadingState = MyLoading.MyLoadingState.Stop
        LoadConfigToUi()
        Configure(Page)
    End Sub

    Public Sub ShowDroppedFiles(files As IEnumerable(Of String))
        If files Is Nothing Then Return
        AppendLog("拖放文件：" & String.Join(", ", files.Select(Function(path) IO.Path.GetFileName(path))))
    End Sub

    Private Sub LoadConfigToUi()
        CurrentConfig = CoreBridge.LoadConfig()

        TxtShareCode.Text = CurrentConfig.ShareCode
        TxtRaceCount.Text = CurrentConfig.RaceCount.ToString()
        TxtBuyCount.Text = CurrentConfig.BuyCount.ToString()
        TxtCjCount.Text = CurrentConfig.CjCount.ToString()
        TxtScCount.Text = CurrentConfig.ScCount.ToString()
        Chk1.Checked = CurrentConfig.Chk1
        Chk2.Checked = CurrentConfig.Chk2
        Chk3.Checked = CurrentConfig.Chk3
        Chk4.Checked = CurrentConfig.Chk4
        TxtNext1.Text = CurrentConfig.Next1.ToString()
        TxtNext2.Text = CurrentConfig.Next2.ToString()
        TxtNext3.Text = CurrentConfig.Next3.ToString()
        TxtNext4.Text = CurrentConfig.Next4.ToString()
        TxtGlobalLoops.Text = CurrentConfig.GlobalLoops.ToString()
        TxtSkillDirs.Text = String.Join(",", CurrentConfig.SkillDirs)
        ChkAutoRestart.Checked = CurrentConfig.AutoRestart
        TxtRestartCmd.Text = CurrentConfig.RestartCommand
        TxtCalcA.Text = CurrentConfig.CalcA
        TxtCalcB.Text = CurrentConfig.CalcB
        TxtCalcC.Text = CurrentConfig.CalcC
        CmbSellMode.SelectedIndex = If(CurrentConfig.SellMode = 2, 1, 0)
        LabConfigPath.Text = "配置文件：" & CoreBridge.ConfigPath
        LabRuntimeInfo.Text = $"项目目录：{CoreBridge.ProjectRoot}{Environment.NewLine}核心启动：{CoreBridge.LaunchMode}"
    End Sub

    Private Function ReadUiConfig() As FH6AutoConfig
        Dim cfg As New FH6AutoConfig With {
            .ShareCode = OnlyDigits(TxtShareCode.Text, "890169683"),
            .RaceCount = ReadInt(TxtRaceCount.Text, 99, 1, 999),
            .BuyCount = ReadInt(TxtBuyCount.Text, 30, 0, 999),
            .CjCount = ReadInt(TxtCjCount.Text, 30, 0, 999),
            .ScCount = ReadInt(TxtScCount.Text, 30, 0, 999),
            .Chk1 = Chk1.Checked,
            .Chk2 = Chk2.Checked,
            .Chk3 = Chk3.Checked,
            .Chk4 = Chk4.Checked,
            .Next1 = ReadInt(TxtNext1.Text, 2, 1, 4),
            .Next2 = ReadInt(TxtNext2.Text, 3, 1, 4),
            .Next3 = ReadInt(TxtNext3.Text, 4, 1, 4),
            .Next4 = ReadInt(TxtNext4.Text, 1, 1, 4),
            .GlobalLoops = ReadInt(TxtGlobalLoops.Text, 10, 1, 999),
            .AutoRestart = ChkAutoRestart.Checked,
            .RestartCommand = If(TxtRestartCmd.Text, "").Trim(),
            .SellMode = If(CmbSellMode.SelectedIndex = 1, 2, 1),
            .CalcA = If(TxtCalcA.Text, "").Trim(),
            .CalcB = If(TxtCalcB.Text, "81700").Trim(),
            .CalcC = If(TxtCalcC.Text, "30").Trim()
        }

        cfg.SkillDirs = TxtSkillDirs.Text.Split({","c, " "c, ";"c}, StringSplitOptions.RemoveEmptyEntries).
            Select(Function(x) x.Trim().ToLowerInvariant()).
            Where(Function(x) {"up", "down", "left", "right"}.Contains(x)).
            ToList()
        If cfg.SkillDirs.Count = 0 Then cfg.SkillDirs = New List(Of String) From {"right", "up", "up", "up", "left"}
        Return cfg
    End Function

    Private Function ReadInt(raw As String, fallback As Integer, min As Integer, max As Integer) As Integer
        Dim value As Integer
        If Not Integer.TryParse(OnlyDigits(raw, fallback.ToString()), value) Then value = fallback
        Return Math.Max(min, Math.Min(max, value))
    End Function

    Private Function OnlyDigits(raw As String, fallback As String) As String
        Dim value = New String(If(raw, "").Where(Function(ch) Char.IsDigit(ch)).ToArray())
        If String.IsNullOrWhiteSpace(value) Then Return fallback
        Return value
    End Function

    Private Sub SaveCurrentConfig()
        CurrentConfig = ReadUiConfig()
        CoreBridge.SaveConfig(CurrentConfig)
        LoadConfigToUi()
    End Sub

    Private Sub StartStep(stepName As String)
        CurrentConfig = ReadUiConfig()
        CoreBridge.StartPipeline(stepName, CurrentConfig)
        EnsureOverlay()
        Overlay.Show()
    End Sub

    Private Sub BtnStartRace_Click(sender As Object, e As MouseButtonEventArgs)
        StartStep("race")
    End Sub

    Private Sub BtnStartBuy_Click(sender As Object, e As MouseButtonEventArgs)
        StartStep("buy")
    End Sub

    Private Sub BtnStartCj_Click(sender As Object, e As MouseButtonEventArgs)
        StartStep("cj")
    End Sub

    Private Sub BtnStartSell_Click(sender As Object, e As MouseButtonEventArgs)
        StartStep("sell")
    End Sub

    Private Sub BtnStop_Click(sender As Object, e As MouseButtonEventArgs)
        CoreBridge.StopPipeline()
    End Sub

    Private Sub BtnSaveConfig_Click(sender As Object, e As MouseButtonEventArgs)
        SaveCurrentConfig()
        Hint("配置已保存。", HintType.Green)
    End Sub

    Private Sub BtnReloadConfig_Click(sender As Object, e As MouseButtonEventArgs)
        LoadConfigToUi()
        Hint("配置已重新加载。", HintType.Blue)
    End Sub

    Private Sub BtnShowOverlay_Click(sender As Object, e As MouseButtonEventArgs)
        EnsureOverlay()
        Overlay.Show()
        Overlay.Activate()
    End Sub

    Private Sub BtnHideOverlay_Click(sender As Object, e As MouseButtonEventArgs)
        If Overlay IsNot Nothing Then Overlay.Hide()
    End Sub

    Private Sub EnsureOverlay()
        If Overlay IsNot Nothing AndAlso Overlay.IsLoaded Then Return
        Overlay = New OverlayWindow()
        Overlay.Owner = FrmMain
    End Sub

    Private Sub OnCoreLog(line As String)
        Dispatcher.Invoke(Sub()
                              AppendLog(line)
                          End Sub)
    End Sub

    Private Sub OnCoreStateChanged(isRunning As Boolean)
        Dispatcher.Invoke(Sub()
                              RefreshStateLabel()
                          End Sub)
    End Sub

    Private Sub AppendLog(line As String)
        TxtLog.AppendText(line & Environment.NewLine)
        TxtLog.ScrollToEnd()
        RefreshStateLabel()
    End Sub

    Private Sub RefreshStateLabel()
        If CoreBridge.IsRunning Then
            LabStatus.Text = "核心状态：运行中"
            LoadState.State.LoadingState = MyLoading.MyLoadingState.Run
        Else
            LabStatus.Text = "核心状态：空闲"
            LoadState.State.LoadingState = MyLoading.MyLoadingState.Stop
        End If
    End Sub
End Class
