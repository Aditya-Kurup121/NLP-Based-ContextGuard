<#
Deploy the ContextGuard API to Google Cloud Run. Safe to re-run: later runs
update the service with your latest code.

  powershell -ExecutionPolicy Bypass -File deploy\deploy-cloudrun.ps1 `
      -Project my-project-id -ModelRepo your-name/contextguard-models

Add -CorsOrigins "https://your-app.vercel.app" once the frontend is deployed.
Run from the project root, after `gcloud init`.
#>
param(
    [Parameter(Mandatory = $true)] [string] $Project,
    [Parameter(Mandatory = $true)] [string] $ModelRepo,
    [string] $CorsOrigins = "http://localhost:5173",
    [string] $CorsOriginRegex = "",
    [string] $Region = "asia-south1",
    [string] $Service = "contextguard-api",
    [switch] $UpdateToken
)

# No ErrorActionPreference=Stop: in Windows PowerShell 5.1 it turns harmless gcloud
# stderr output into errors. Failures are caught through $LASTEXITCODE instead.
function Invoke-Gcloud {
    & gcloud @args
    if ($LASTEXITCODE -ne 0) { throw "gcloud $($args -join ' ') failed" }
}

if (-not (Test-Path "Dockerfile")) { throw "Run this from the project root (the folder with Dockerfile)." }

Write-Host "== Project $Project, region $Region"
Invoke-Gcloud config set project $Project --quiet

Write-Host "== Enabling APIs (first run takes a minute)"
Invoke-Gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com

$number = "$(& gcloud projects describe $Project --format="value(projectNumber)")".Trim()
if (-not $number) { throw "Project '$Project' not found. Use the Project ID shown in the Cloud Console." }
$serviceAccount = "$number-compute@developer.gserviceaccount.com"

# The Hugging Face read token lives in Secret Manager, never in the image or the command line.
$exists = [bool](& gcloud secrets list --filter="name~hf-token$" --format="value(name)")
if (-not $exists -or $UpdateToken) {
    $secure = Read-Host "Paste a READ-only Hugging Face token (input hidden)" -AsSecureString
    $token = [System.Net.NetworkCredential]::new("", $secure).Password.Trim()
    if (-not $token.StartsWith("hf_")) { throw "That doesn't look like a Hugging Face token (should start with hf_)." }
    $tmp = New-TemporaryFile
    try {
        [System.IO.File]::WriteAllText($tmp.FullName, $token)
        if ($exists) { Invoke-Gcloud secrets versions add hf-token --data-file="$($tmp.FullName)" }
        else { Invoke-Gcloud secrets create hf-token --replication-policy=automatic --data-file="$($tmp.FullName)" }
    } finally { Remove-Item $tmp.FullName -Force }
}

Write-Host "== Granting the service account access to the token and to source builds"
Invoke-Gcloud secrets add-iam-policy-binding hf-token --member="serviceAccount:$serviceAccount" --role=roles/secretmanager.secretAccessor --format=none --quiet
Invoke-Gcloud projects add-iam-policy-binding $Project --member="serviceAccount:$serviceAccount" --role=roles/run.builder --condition=None --format=none --quiet

# Settings go through a YAML file: gcloud on Windows is a .cmd script, and cmd.exe
# mangles characters such as ^ , | & in command-line values.
function Quote([string] $value) { "'" + $value.Replace("'", "''") + "'" }
$envLines = @("MODEL_REPO: $(Quote $ModelRepo)", "CORS_ORIGINS: $(Quote $CorsOrigins)")
if ($CorsOriginRegex) { $envLines += "CORS_ORIGIN_REGEX: $(Quote $CorsOriginRegex)" }
$envFile = Join-Path ([System.IO.Path]::GetTempPath()) "contextguard-env.yaml"
[System.IO.File]::WriteAllLines($envFile, $envLines)

Write-Host "== Building and deploying (about 10 minutes the first time)"
# 2 GiB: Cloud Run keeps downloaded files in memory (~530 MB of weights) on top of ~450 MB for the loaded models.
# min-instances 0: no cost while idle. max-instances 2: caps spending.
Invoke-Gcloud run deploy $Service `
    --source . `
    --region $Region `
    --allow-unauthenticated `
    --memory 2Gi --cpu 1 --cpu-boost `
    --min-instances 0 --max-instances 2 `
    --concurrency 20 --timeout 300 `
    --env-vars-file "$envFile" `
    --set-secrets HF_TOKEN=hf-token:latest `
    --quiet
Remove-Item $envFile -Force

$url = "$(& gcloud run services describe $Service --region $Region --format="value(status.url)")".Trim()
Write-Host ""
Write-Host "Deployed: $url"
Write-Host "API docs: $url/docs"
Write-Host "Set VITE_API_URL on Vercel to: $url/api"
