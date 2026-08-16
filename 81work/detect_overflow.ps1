# Detect real text overflow via PowerPoint COM (ASCII-only paths/labels)
$ErrorActionPreference = "Stop"
$ppt = New-Object -ComObject PowerPoint.Application
try {
  $pres = $ppt.Presentations.Open("e:\wenan catch\81work\deck_out.pptx", $true, $false, $false)
  $slideH = 540.0
  $overflow = @()
  $offpage = @()
  foreach ($slide in $pres.Slides) {
    $si = $slide.SlideIndex
    foreach ($shape in $slide.Shapes) {
      if ($shape.HasTextFrame -eq -1) {
        $tf = $shape.TextFrame
        if ($tf.HasText -eq -1) {
          $tr = $tf.TextRange
          $bh = [double]$tr.BoundHeight
          $bt = [double]$tr.BoundTop
          if ($bh -gt 0) {
            $sTop = [double]$shape.Top
            $sH = [double]$shape.Height
            # BoundTop/BoundHeight are ABSOLUTE from slide top
            $textBottomAbs = $bt + $bh
            $shapeBottom = $sTop + $sH
            $txt = [string]$shape.TextFrame.TextRange.Text
            if ($txt.Length -gt 18) { $txt = $txt.Substring(0,18) }
            $txt = $txt.Replace("`r","/").Replace("`n","/")
            if ($textBottomAbs -gt ($shapeBottom + 4)) {
              $overflow += [pscustomobject]@{ Slide=$si; Txt=$txt; SB=[Math]::Round($shapeBottom,1); TB=[Math]::Round($textBottomAbs,1); Bh=[Math]::Round($bh,1) }
            }
            if ($textBottomAbs -gt ($slideH + 3)) {
              $offpage += [pscustomobject]@{ Slide=$si; Txt=$txt; TB=[Math]::Round($textBottomAbs,1) }
            }
          }
        }
      }
    }
  }
  $pres.Close()
  Write-Output ("OVERFLOW-SHAPE count: " + $overflow.Count)
  foreach ($o in $overflow) {
    Write-Output ("slide {0} shapeBottom {1}pt textBottom {2}pt (textH {3}pt) | {4}" -f $o.Slide,$o.SB,$o.TB,$o.Bh,$o.Txt)
  }
  Write-Output ("OFFPAGE count: " + $offpage.Count)
  foreach ($o in $offpage) {
    Write-Output ("slide {0} textBottom {1}pt | {2}" -f $o.Slide,$o.TB,$o.Txt)
  }
} finally {
  $ppt.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null
}
