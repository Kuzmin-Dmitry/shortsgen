# Final Audio Service Test
Write-Host "=== Final Audio Service Test ===" -ForegroundColor Green

# Test data
$testData = @{
    text = "Тестирование сервиса генерации аудио для проекта ShortsGen"
    language = "ru"
    voice = "alloy"
    format = "mp3"
    mock = $true
} | ConvertTo-Json

Write-Host "Request Data:" -ForegroundColor Yellow
Write-Host $testData

try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8003/generateAudio" -Method Post -Body $testData -ContentType "application/json"
    
    Write-Host "`nResponse:" -ForegroundColor Yellow
    Write-Host "Success: $($response.success)" -ForegroundColor Green
    Write-Host "Message: $($response.message)" -ForegroundColor Green
    Write-Host "File Size: $($response.file_size_kb) KB"
    Write-Host "Duration: $($response.duration_seconds) seconds"
    
    if ($response.error) {
        Write-Host "Error: $($response.error)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "Request failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Green
