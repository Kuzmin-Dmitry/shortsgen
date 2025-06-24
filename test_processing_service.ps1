# Тест Processing Service
$baseUrl = "http://localhost:8001"

# Создание сценария
Write-Host "=== Создание сценария CreateVoice ===" -ForegroundColor Green
$response = Invoke-RestMethod -Uri "$baseUrl/generate" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"scenario":"CreateVoice"}'
$scenarioId = $response.scenario_id
Write-Host "Scenario ID: $scenarioId"

# Получение сценария
Write-Host "`n=== Получение сценария ===" -ForegroundColor Green
$scenario = Invoke-RestMethod -Uri "$baseUrl/getScenario/$scenarioId" -Method GET
$scenario | ConvertTo-Json -Depth 3

# Health check
Write-Host "`n=== Health Check ===" -ForegroundColor Green
$health = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
$health | ConvertTo-Json
