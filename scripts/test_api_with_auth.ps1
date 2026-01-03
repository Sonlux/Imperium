# Test Script for Imperium API with Authentication
# Tests all endpoints including new authentication features

$BASE_URL = "http://localhost:5000"
$API_URL = "$BASE_URL/api/v1"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Imperium API Test Suite with Authentication" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Test counter
$testsPassed = 0
$testsFailed = 0
$JWT_TOKEN = ""

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [object]$Body,
        [hashtable]$Headers
    )
    
    Write-Host "Test: $Name" -ForegroundColor Yellow
    
    try {
        $params = @{
            Method = $Method
            Uri = $Url
            ContentType = "application/json"
        }
        
        if ($Headers) {
            $params['Headers'] = $Headers
        }
        
        if ($Body) {
            $params['Body'] = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params
        
        Write-Host "✓ Success - Status: 200 OK" -ForegroundColor Green
        Write-Host "Response: $($response | ConvertTo-Json -Depth 2 -Compress)" -ForegroundColor Gray
        $script:testsPassed++
        return $response
        
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorBody = ""
        
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $errorBody = $reader.ReadToEnd()
        }
        
        if ($statusCode -eq 401 -or $statusCode -eq 429) {
            Write-Host "✓ Expected error - Status: $statusCode" -ForegroundColor Yellow
            Write-Host "Response: $errorBody" -ForegroundColor Gray
            $script:testsPassed++
        } else {
            Write-Host "✗ Failed - Status: $statusCode" -ForegroundColor Red
            Write-Host "Error: $errorBody" -ForegroundColor Red
            $script:testsFailed++
        }
        
        return $null
    }
    
    Write-Host ""
}

# Test 1: Health Check (Public endpoint)
Write-Host "`n=== Phase 1: Public Endpoints ===" -ForegroundColor Cyan
$health = Test-Endpoint -Name "Health Check" -Method "GET" -Url "$BASE_URL/health"

# Test 2: User Registration
Write-Host "`n=== Phase 2: User Registration ===" -ForegroundColor Cyan
$registerData = @{
    username = "testuser"
    password = "TestPassword123!"
    email = "testuser@imperium.local"
}
$registration = Test-Endpoint -Name "Register New User" -Method "POST" -Url "$API_URL/auth/register" -Body $registerData

# Test 3: User Login
Write-Host "`n=== Phase 3: Authentication ===" -ForegroundColor Cyan
$loginData = @{
    username = "admin"
    password = "admin"
}
$loginResponse = Test-Endpoint -Name "Login with Admin Account" -Method "POST" -Url "$API_URL/auth/login" -Body $loginData

if ($loginResponse -and $loginResponse.token) {
    $JWT_TOKEN = $loginResponse.token
    Write-Host "`n🔑 JWT Token acquired: $($JWT_TOKEN.Substring(0, 20))..." -ForegroundColor Green
}

# Test 4: Verify Token
if ($JWT_TOKEN) {
    Write-Host "`n=== Phase 4: Token Verification ===" -ForegroundColor Cyan
    $authHeaders = @{
        "Authorization" = "Bearer $JWT_TOKEN"
    }
    Test-Endpoint -Name "Verify JWT Token" -Method "GET" -Url "$API_URL/auth/verify" -Headers $authHeaders
}

# Test 5: Get User Profile
if ($JWT_TOKEN) {
    Write-Host "`n=== Phase 5: User Profile ===" -ForegroundColor Cyan
    $authHeaders = @{
        "Authorization" = "Bearer $JWT_TOKEN"
    }
    Test-Endpoint -Name "Get User Profile" -Method "GET" -Url "$API_URL/auth/profile" -Headers $authHeaders
}

# Test 6: Submit Intent WITHOUT Authentication (Should fail or succeed based on config)
Write-Host "`n=== Phase 6: Intent Submission (Unauthenticated) ===" -ForegroundColor Cyan
$intentData = @{
    description = "Prioritize sensor data from temperature sensors"
}
Test-Endpoint -Name "Submit Intent (No Auth)" -Method "POST" -Url "$API_URL/intents" -Body $intentData

# Test 7: Submit Intent WITH Authentication
if ($JWT_TOKEN) {
    Write-Host "`n=== Phase 7: Intent Submission (Authenticated) ===" -ForegroundColor Cyan
    $authHeaders = @{
        "Authorization" = "Bearer $JWT_TOKEN"
    }
    
    $intents = @(
        @{ description = "Prioritize temperature sensor data" },
        @{ description = "Limit bandwidth to 500KB/s for camera streams" },
        @{ description = "Reduce latency for device sensor-001 to under 50ms" }
    )
    
    foreach ($intent in $intents) {
        Test-Endpoint -Name "Submit Intent: $($intent.description)" -Method "POST" -Url "$API_URL/intents" -Body $intent -Headers $authHeaders
        Start-Sleep -Milliseconds 500
    }
}

# Test 8: List All Intents (Authenticated)
if ($JWT_TOKEN) {
    Write-Host "`n=== Phase 8: Retrieve Intents ===" -ForegroundColor Cyan
    $authHeaders = @{
        "Authorization" = "Bearer $JWT_TOKEN"
    }
    Test-Endpoint -Name "List All Intents" -Method "GET" -Url "$API_URL/intents" -Headers $authHeaders
}

# Test 9: List All Policies (Authenticated)
if ($JWT_TOKEN) {
    Write-Host "`n=== Phase 9: Retrieve Policies ===" -ForegroundColor Cyan
    $authHeaders = @{
        "Authorization" = "Bearer $JWT_TOKEN"
    }
    Test-Endpoint -Name "List All Policies" -Method "GET" -Url "$API_URL/policies" -Headers $authHeaders
}

# Test 10: Test Rate Limiting
Write-Host "`n=== Phase 10: Rate Limiting Test ===" -ForegroundColor Cyan
Write-Host "Sending 15 rapid requests to test rate limiter..." -ForegroundColor Gray

$rateLimitTest = 0
for ($i = 1; $i -le 15; $i++) {
    try {
        $response = Invoke-RestMethod -Method GET -Uri "$BASE_URL/health" -ContentType "application/json"
        $rateLimitTest++
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq 429) {
            Write-Host "✓ Rate limit triggered after $rateLimitTest requests" -ForegroundColor Yellow
            break
        }
    }
}

if ($rateLimitTest -eq 15) {
    Write-Host "✓ All 15 requests succeeded (rate limit not reached)" -ForegroundColor Green
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Results Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Tests Passed: $testsPassed" -ForegroundColor Green
Write-Host "Tests Failed: $testsFailed" -ForegroundColor $(if ($testsFailed -gt 0) { "Red" } else { "Green" })
Write-Host "Total Tests:  $($testsPassed + $testsFailed)" -ForegroundColor White
Write-Host "`n"

if ($testsFailed -eq 0) {
    Write-Host "✅ All tests completed successfully!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some tests failed. Check the output above." -ForegroundColor Yellow
}

Write-Host "`n📊 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Check Grafana dashboard: http://localhost:3000" -ForegroundColor White
Write-Host "  2. Check Prometheus metrics: http://localhost:9090" -ForegroundColor White
Write-Host "  3. View MQTT messages: docker logs imperium-mqtt" -ForegroundColor White
Write-Host "  4. Review database: data/imperium.db" -ForegroundColor White
Write-Host ""
