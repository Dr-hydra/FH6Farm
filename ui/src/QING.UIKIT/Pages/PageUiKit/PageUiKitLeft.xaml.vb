Public Class PageUiKitLeft

    Private CurrentPage As UiKitDemoPage = UiKitDemoPage.Overview
    Private CurrentRight As PageUiKitRight

    Public Sub Configure(page As UiKitDemoPage, rightPage As PageUiKitRight)
        CurrentPage = page
        CurrentRight = rightPage
        LabSection.Text = UiKitShellText.GetPageTitle(page)
        LabDescription.Text = CurrentRight?.Subtitle
        SetChecked(page)
    End Sub

    Private Sub SetChecked(page As UiKitDemoPage)
        Dim items = {ItemOverview, ItemControls, ItemLayout, ItemTheme, ItemAbout}
        For Each item In items
            item.SetChecked(CInt(item.Tag) = CInt(page), False, False)
        Next
    End Sub

    Private Sub NavItem_Check(sender As Object, e As RouteEventArgs) Handles ItemOverview.Check, ItemControls.Check, ItemLayout.Check, ItemTheme.Check, ItemAbout.Check
        Dim item = TryCast(sender, FrameworkElement)
        If item Is Nothing OrElse item.Tag Is Nothing OrElse FrmMain Is Nothing Then Return
        Dim page = CType(Val(item.Tag), UiKitDemoPage)
        If page = CurrentPage Then Return
        FrmMain.PageChange(page)
    End Sub

End Class
