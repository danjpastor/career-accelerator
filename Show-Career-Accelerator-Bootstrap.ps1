param(
    [Parameter(Mandatory = $true)]
    [string]$RepositoryPath,

    [Parameter(Mandatory = $true)]
    [string]$StatusPath,

    [Parameter(Mandatory = $true)]
    [string]$ReadyPath
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase

$repo = [System.IO.Path]::GetFullPath($RepositoryPath)
$brushConverter = New-Object System.Windows.Media.BrushConverter

function Get-Brush {
    param([string]$Value)
    return $brushConverter.ConvertFromString($Value)
}

function Get-SelectedPathway {
    $candidates = @(
        (Join-Path $repo "data\onboarding_state.json"),
        (Join-Path $repo "application\data\onboarding_state.json")
    )

    foreach ($candidate in $candidates) {
        if (-not (Test-Path -LiteralPath $candidate)) {
            continue
        }

        try {
            $payload = Get-Content -LiteralPath $candidate -Raw | ConvertFrom-Json

            if ($payload.selected_pathway_id) {
                return [string]$payload.selected_pathway_id
            }

            if ($payload.pathway_id) {
                return [string]$payload.pathway_id
            }
        }
        catch {
        }
    }

    return ""
}

function Get-LogoPath {
    $assetRoot = Join-Path $repo "application\assets\pathways"
    $pathway = Get-SelectedPathway

    switch ($pathway) {
        "data_analytics" {
            return Join-Path $assetRoot "data_analytics_stacked.png"
        }
        "it_support" {
            return Join-Path $assetRoot "it_support_stacked.png"
        }
        "cybersecurity" {
            return Join-Path $assetRoot "cybersecurity_stacked.png"
        }
        "software_engineering" {
            return Join-Path $assetRoot "software_engineering_stacked.png"
        }
        default {
            return Join-Path $assetRoot "career_accelerator_stacked.png"
        }
    }
}

$window = New-Object System.Windows.Window
$window.Width = 760
$window.Height = 560
$window.MinWidth = 700
$window.MinHeight = 520
$window.SizeToContent = [System.Windows.SizeToContent]::Manual
$window.WindowStyle = [System.Windows.WindowStyle]::None
$window.ResizeMode = [System.Windows.ResizeMode]::NoResize
$window.AllowsTransparency = $true
$window.Background = [System.Windows.Media.Brushes]::Transparent
$window.Topmost = $true
$window.ShowInTaskbar = $false
$window.WindowStartupLocation = [System.Windows.WindowStartupLocation]::CenterScreen

$shell = New-Object System.Windows.Controls.Border
$shell.CornerRadius = New-Object System.Windows.CornerRadius -ArgumentList 28
$shell.Background = Get-Brush "#07122C"
$shell.BorderBrush = Get-Brush "#4C7DFF"
$shell.BorderThickness = New-Object System.Windows.Thickness -ArgumentList 2
$shell.Padding = New-Object System.Windows.Thickness -ArgumentList 40,30,40,28
$shell.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Stretch
$shell.VerticalAlignment = [System.Windows.VerticalAlignment]::Stretch
$window.Content = $shell

$layout = New-Object System.Windows.Controls.StackPanel
$layout.Orientation = [System.Windows.Controls.Orientation]::Vertical
$layout.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Stretch
$shell.Child = $layout

$logo = New-Object System.Windows.Controls.Image
$logo.Height = 252
$logo.Stretch = [System.Windows.Media.Stretch]::Uniform
$logo.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Stretch
$logo.Margin = New-Object System.Windows.Thickness -ArgumentList 8,0,8,8

$logoPath = Get-LogoPath

if (Test-Path -LiteralPath $logoPath) {
    try {
        $bitmap = New-Object System.Windows.Media.Imaging.BitmapImage
        $bitmap.BeginInit()
        $bitmap.CacheOption = [System.Windows.Media.Imaging.BitmapCacheOption]::OnLoad
        $bitmap.UriSource = New-Object System.Uri -ArgumentList $logoPath
        $bitmap.EndInit()
        $bitmap.Freeze()
        $logo.Source = $bitmap
    }
    catch {
    }
}

$layout.Children.Add($logo) | Out-Null

$title = New-Object System.Windows.Controls.TextBlock
$title.Text = "Starting Career Accelerator"
$title.Foreground = Get-Brush "#FFFFFF"
$title.FontSize = 26
$title.FontWeight = [System.Windows.FontWeights]::Bold
$title.TextAlignment = [System.Windows.TextAlignment]::Center
$title.TextWrapping = [System.Windows.TextWrapping]::Wrap
$title.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Stretch
$title.Margin = New-Object System.Windows.Thickness -ArgumentList 8,0,8,8
$layout.Children.Add($title) | Out-Null

$subtitle = New-Object System.Windows.Controls.TextBlock
$subtitle.Text = "Preparing your 90-day career plan."
$subtitle.Foreground = Get-Brush "#AAB8D1"
$subtitle.FontSize = 15
$subtitle.TextAlignment = [System.Windows.TextAlignment]::Center
$subtitle.TextWrapping = [System.Windows.TextWrapping]::Wrap
$subtitle.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Stretch
$subtitle.Margin = New-Object System.Windows.Thickness -ArgumentList 8,0,8,20
$layout.Children.Add($subtitle) | Out-Null

$progressTrack = New-Object System.Windows.Controls.Border
$progressTrack.Height = 22
$progressTrack.MinWidth = 100
$progressTrack.CornerRadius = New-Object System.Windows.CornerRadius -ArgumentList 11
$progressTrack.Background = Get-Brush "#0B1732"
$progressTrack.BorderBrush = Get-Brush "#344A72"
$progressTrack.BorderThickness = New-Object System.Windows.Thickness -ArgumentList 1
$progressTrack.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Stretch
$progressTrack.Margin = New-Object System.Windows.Thickness -ArgumentList 8,0,8,18

$progressGrid = New-Object System.Windows.Controls.Grid
$progressGrid.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Stretch
$progressTrack.Child = $progressGrid

$progressFill = New-Object System.Windows.Controls.Border
$progressFill.Height = 20
$progressFill.Width = 8
$progressFill.CornerRadius = New-Object System.Windows.CornerRadius -ArgumentList 10
$progressFill.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Left

$gradient = New-Object System.Windows.Media.LinearGradientBrush
$gradient.StartPoint = New-Object System.Windows.Point -ArgumentList 0,0.5
$gradient.EndPoint = New-Object System.Windows.Point -ArgumentList 1,0.5

$stop1 = New-Object System.Windows.Media.GradientStop
$stop1.Color = [System.Windows.Media.ColorConverter]::ConvertFromString("#4C7DFF")
$stop1.Offset = 0.0
$gradient.GradientStops.Add($stop1)

$stop2 = New-Object System.Windows.Media.GradientStop
$stop2.Color = [System.Windows.Media.ColorConverter]::ConvertFromString("#9A5CFF")
$stop2.Offset = 0.55
$gradient.GradientStops.Add($stop2)

$stop3 = New-Object System.Windows.Media.GradientStop
$stop3.Color = [System.Windows.Media.ColorConverter]::ConvertFromString("#F33AAE")
$stop3.Offset = 1.0
$gradient.GradientStops.Add($stop3)

$progressFill.Background = $gradient
$progressGrid.Children.Add($progressFill) | Out-Null
$layout.Children.Add($progressTrack) | Out-Null

$statusGrid = New-Object System.Windows.Controls.Grid
$statusGrid.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Stretch
$statusGrid.Margin = New-Object System.Windows.Thickness -ArgumentList 8,0,8,0

$leftColumn = New-Object System.Windows.Controls.ColumnDefinition
$leftColumn.Width = New-Object System.Windows.GridLength -ArgumentList 1,Star
$statusGrid.ColumnDefinitions.Add($leftColumn)

$rightColumn = New-Object System.Windows.Controls.ColumnDefinition
$rightColumn.Width = [System.Windows.GridLength]::Auto
$statusGrid.ColumnDefinitions.Add($rightColumn)

$statusText = New-Object System.Windows.Controls.TextBlock
$statusText.Text = "Starting application..."
$statusText.Foreground = Get-Brush "#FFFFFF"
$statusText.FontSize = 16
$statusText.FontWeight = [System.Windows.FontWeights]::SemiBold
$statusText.TextTrimming = [System.Windows.TextTrimming]::CharacterEllipsis
$statusText.TextWrapping = [System.Windows.TextWrapping]::NoWrap
$statusText.MinWidth = 0
$statusText.Margin = New-Object System.Windows.Thickness -ArgumentList 0,0,10,0
[System.Windows.Controls.Grid]::SetColumn($statusText, 0)
$statusGrid.Children.Add($statusText) | Out-Null

$stepText = New-Object System.Windows.Controls.TextBlock
$stepText.Text = "Step 1 of 8"
$stepText.Foreground = Get-Brush "#A85CFF"
$stepText.FontSize = 14
$stepText.FontWeight = [System.Windows.FontWeights]::Bold
$stepText.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Right
$stepText.Margin = New-Object System.Windows.Thickness -ArgumentList 8,0,0,0
[System.Windows.Controls.Grid]::SetColumn($stepText, 1)
$statusGrid.Children.Add($stepText) | Out-Null

$layout.Children.Add($statusGrid) | Out-Null

$detailText = New-Object System.Windows.Controls.TextBlock
$detailText.Text = "Checking the local application environment."
$detailText.Foreground = Get-Brush "#AAB8D1"
$detailText.FontSize = 13
$detailText.TextAlignment = [System.Windows.TextAlignment]::Left
$detailText.TextWrapping = [System.Windows.TextWrapping]::Wrap
$detailText.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Stretch
$detailText.Height = 44
$detailText.Margin = New-Object System.Windows.Thickness -ArgumentList 8,8,8,0
$layout.Children.Add($detailText) | Out-Null

$footer = New-Object System.Windows.Controls.TextBlock
$footer.Text = "No console window is required."
$footer.Foreground = Get-Brush "#AAB8D1"
$footer.FontSize = 13
$footer.TextAlignment = [System.Windows.TextAlignment]::Center
$footer.TextWrapping = [System.Windows.TextWrapping]::Wrap
$footer.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Stretch
$footer.Margin = New-Object System.Windows.Thickness -ArgumentList 8,14,8,0
$layout.Children.Add($footer) | Out-Null

$script:lastMessage = ""
$script:lastDetail = ""
$script:lastPercent = 5
$script:lastStep = 1
$script:lastTotalSteps = 8
$script:dotFrame = 0

$timer = New-Object System.Windows.Threading.DispatcherTimer
$timer.Interval = [TimeSpan]::FromMilliseconds(160)

$timer.Add_Tick({
    $script:dotFrame = ($script:dotFrame + 1) % 4

    if (Test-Path -LiteralPath $StatusPath) {
        try {
            $payload = Get-Content -LiteralPath $StatusPath -Raw | ConvertFrom-Json

            if ($null -ne $payload.message) {
                $script:lastMessage = [string]$payload.message
            }

            if ($null -ne $payload.detail) {
                $script:lastDetail = [string]$payload.detail
            }

            if ($null -ne $payload.percent) {
                $script:lastPercent = [int]$payload.percent
            }

            if ($null -ne $payload.step) {
                $script:lastStep = [int]$payload.step
            }

            if ($null -ne $payload.total_steps) {
                $script:lastTotalSteps = [int]$payload.total_steps
            }

            if ([string]$payload.state -eq "close") {
                $timer.Stop()
                $window.Close()
                return
            }

            if ([string]$payload.state -eq "error") {
                $statusText.Foreground = Get-Brush "#FF6B81"
            }
            else {
                $statusText.Foreground = Get-Brush "#FFFFFF"
            }
        }
        catch {
        }
    }

    $dots = ""

    if ($script:dotFrame -gt 0) {
        $dots = "." * $script:dotFrame
    }

    $statusText.Text = $script:lastMessage + $dots
    $detailText.Text = $script:lastDetail
    $stepText.Text = "Step $($script:lastStep) of $($script:lastTotalSteps)"

    $clamped = [Math]::Max(0, [Math]::Min(100, $script:lastPercent))
    $availableWidth = [Math]::Max(8, $progressTrack.ActualWidth - 2)
    $progressFill.Width = [Math]::Max(8, $availableWidth * ($clamped / 100.0))
})

$window.Add_Loaded({
    try {
        Set-Content -LiteralPath $ReadyPath -Value "ready" -Encoding UTF8
    }
    catch {
    }

    $timer.Start()
})

$window.Add_Closed({
    $timer.Stop()
})

$null = $window.ShowDialog()
