# Processing Service Test
$baseUrl = "http://localhost:8001"

Write-Host "=== PROCESSING SERVICE TESTS ===" -ForegroundColor Cyan

# 1. Health check
Write-Host "`n[Health Check]" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    Write-Host "Payload: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
    Write-Host "PASS - Status: $($response.status)" -ForegroundColor Green
} catch {
    Write-Host "FAIL - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. Create scenario
Write-Host "`n[Create Scenario]" -ForegroundColor Yellow
try {
    $request = @{ scenario = "CreateText" } | ConvertTo-Json
    $scenario = Invoke-RestMethod -Uri "$baseUrl/generate" -Method Post -Body $request -ContentType "application/json"
    Write-Host "Payload: $($scenario | ConvertTo-Json -Compress)" -ForegroundColor Gray
    Write-Host "PASS - Scenario ID: $($scenario.scenario_id), Tasks: $($scenario.tasks.Count)" -ForegroundColor Green
} catch {
    Write-Host "FAIL - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 3. Get scenario by ID
Write-Host "`n[Get Scenario by ID]" -ForegroundColor Yellow
try {
    $scenarioTasks = Invoke-RestMethod -Uri "$baseUrl/getScenario/$($scenario.scenario_id)" -Method Get
    Write-Host "Payload: $($scenarioTasks | ConvertTo-Json -Compress)" -ForegroundColor Gray
    
    # Определяем количество задач (может быть массив или одиночный объект)
    if ($scenarioTasks -is [array]) {
        $taskCount = $scenarioTasks.Count
        $firstTask = $scenarioTasks[0]
    } else {
        $taskCount = 1
        $firstTask = $scenarioTasks
    }
    
    Write-Host "PASS - Retrieved $taskCount tasks" -ForegroundColor Green
} catch {
    Write-Host "FAIL - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 4. Get task by ID
Write-Host "`n[Get Task by ID]" -ForegroundColor Yellow
try {
    $taskId = $firstTask.id
    $task = Invoke-RestMethod -Uri "$baseUrl/getTask/$taskId" -Method Get
    Write-Host "Payload: $($task | ConvertTo-Json -Compress)" -ForegroundColor Gray
    Write-Host "PASS - Task: $($task.task_name), Status: $($task.status)" -ForegroundColor Green
} catch {
    Write-Host "FAIL - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`nAll tests passed!" -ForegroundColor Green
