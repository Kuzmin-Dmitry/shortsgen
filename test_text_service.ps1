# Test text_service
$baseUrl = "http://localhost:8002"

Write-Host "Testing text_service..." -ForegroundColor Yellow

# Health check test
try {
    $healthResponse = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    Write-Host "OK Health check: $($healthResponse.status)" -ForegroundColor Green
} catch {
    Write-Host "FAIL Health check: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Text generation test
$testRequest = @{
    prompt = "Write a short text about a cat"
    max_tokens = 100
    temperature = 0.7
    model = "openai"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/generateText" -Method Post -Body $testRequest -ContentType "application/json"
    
    if ($response.success -and $response.content) {
        Write-Host "OK Text generation successful" -ForegroundColor Green
        Write-Host "Model: $($response.model_used)" -ForegroundColor Cyan
        Write-Host "Tokens: $($response.tokens_generated)" -ForegroundColor Cyan
        Write-Host "Text: $($response.content.Substring(0, [Math]::Min(100, $response.content.Length)))..." -ForegroundColor White
    } else {
        Write-Host "FAIL Text generation failed" -ForegroundColor Red
    }
} catch {
    Write-Host "FAIL Generation error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $errorResponse = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorResponse)
        $errorBody = $reader.ReadToEnd()
        Write-Host "API Response: $errorBody" -ForegroundColor Red
    }
}

Write-Host "Test completed" -ForegroundColor Yellow
