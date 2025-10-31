# Migrate Secrets Pipe

A Bitbucket Pipe that automatically migrates secret variables from Bitbucket to GitHub. This pipe solves the problem that Bitbucket's API doesn't allow retrieving secret values, but during pipeline execution, secrets are available as environment variables.

## Features

- Migrates repository-level secrets from Bitbucket to GitHub
- Migrates environment-specific secrets from Bitbucket to GitHub
- Uses GitHub CLI for secure secret management
- Provides detailed migration summary with success/failure counts

## Prerequisites

1. **GitHub Personal Access Token** with the following scopes:
   - `repo` (Full control of private repositories)
   - `admin:repo_hook` (for repository secrets)

2. **Bitbucket Pipeline Variables** containing the secrets you want to migrate (these must be marked as secured variables in Bitbucket)

## Usage

### Migrating Repository Secrets

To migrate repository-level secrets from Bitbucket to GitHub:

```yaml
pipelines:
  custom:
    migrate-secrets:
      - step:
          name: Migrate Repository Secrets
          script:
            - pipe: aligent/migrate-secrets-pipe:latest
              variables:
                GITHUB_TOKEN: $GITHUB_TOKEN
                GITHUB_REPO: 'owner/repo-name'
                SECRET_NAMES: 'DATABASE_PASSWORD,API_KEY,AWS_SECRET_KEY'
```

### Migrating Environment Secrets

To migrate environment-specific secrets:

```yaml
pipelines:
  custom:
    migrate-production-secrets:
      - step:
          name: Migrate Production Environment Secrets
          deployment: production
          script:
            - pipe: aligent/migrate-secrets-pipe:latest
              variables:
                GITHUB_TOKEN: $GITHUB_TOKEN
                GITHUB_REPO: 'owner/repo-name'
                SECRET_NAMES: 'PROD_DATABASE_PASSWORD,PROD_API_KEY'
                ENVIRONMENT: 'production'
```

### Migrating Multiple Environments

You can create separate pipeline steps for each environment:

```yaml
pipelines:
  custom:
    migrate-all-secrets:
      - step:
          name: Migrate Repository Secrets
          script:
            - pipe: aligent/migrate-secrets-pipe:latest
              variables:
                GITHUB_TOKEN: $GITHUB_TOKEN
                GITHUB_REPO: 'owner/repo-name'
                SECRET_NAMES: 'SHARED_SECRET_1,SHARED_SECRET_2'
                SHARED_SECRET_1: $SHARED_SECRET_1
                SHARED_SECRET_2: $SHARED_SECRET_1

      - step:
          name: Migrate Development Environment Secrets
          deployment: development
          script:
            - pipe: aligent/migrate-secrets-pipe:latest
              variables:
                ENVIRONMENT: 'development'
                GITHUB_TOKEN: $GITHUB_TOKEN
                GITHUB_REPO: 'owner/repo-name'
                SECRET_NAMES: 'DEV_DATABASE_URL,DEV_API_KEY'
                DEV_DATABASE_URL: $DEV_DATABASE_URL
                DEV_API_KEY: $DEV_API_KEY

      - step:
          name: Migrate Staging Environment Secrets
          deployment: staging
          script:
            - pipe: aligent/migrate-secrets-pipe:latest
              variables:
                ENVIRONMENT: 'staging'
                GITHUB_TOKEN: $GITHUB_TOKEN
                GITHUB_REPO: 'owner/repo-name'
                SECRET_NAMES: 'STAGING_DATABASE_URL,STAGING_API_KEY'
                STAGING_DATABASE_URL: $STAGING_DATABASE_URL
                STAGING_API_KEY: $STAGING_API_KEY

      - step:
          name: Migrate Production Environment Secrets
          deployment: production
          script:
            - pipe: aligent/migrate-secrets-pipe:latest
              variables:
                ENVIRONMENT: 'production'
                GITHUB_TOKEN: $GITHUB_TOKEN
                GITHUB_REPO: 'owner/repo-name'
                SECRET_NAMES: 'PROD_DATABASE_URL,PROD_API_KEY'
                PROD_DATABASE_URL: $PROD_DATABASE_URL
                PROD_API_KEY: $PROD_API_KEY 
```

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `GITHUB_TOKEN` | Yes | - | GitHub Personal Access Token with `repo` and `admin:repo_hook` scopes |
| `GITHUB_REPO` | Yes | - | Target GitHub repository in `owner/repo` format |
| `SECRET_NAMES` | Yes | - | Comma-separated list of secret variable names to migrate |
| `ENVIRONMENT` | No | - | GitHub environment name (if migrating environment-specific secrets) |
| `DEBUG` | No | `false` | Enable debug logging (`true`/`false`) |

## How It Works

1. The pipe runs within a Bitbucket Pipeline where secured variables are accessible as environment variables
2. For each secret name provided in `SECRET_NAMES`, the pipe:
   - Reads the value from the Bitbucket pipeline environment variable
   - Uses GitHub CLI (`gh secret set`) to create/update the secret in GitHub
3. Provides a summary of successfully migrated, failed, and missing secrets
4. Exits with an error code if any secrets fail to migrate or are missing

## Important Notes

- **Secret values must exist in Bitbucket**: The secrets you want to migrate must be defined in your Bitbucket repository or deployment environment settings
- **GitHub Token Security**: Store your `GITHUB_TOKEN` as a secured variable in Bitbucket
- **Environment Variables**: When using the `ENVIRONMENT` parameter, make sure the GitHub environment exists or the pipe will create it
- **Naming Convention**: Secret names in Bitbucket and GitHub must match (the pipe uses the same name in both systems)

## Example: Complete Migration Workflow

```yaml
pipelines:
  custom:
    full-migration:
      # Step 1: Migrate repository-level secrets
      - step:
          name: Migrate Repository Secrets
          script:
            - pipe: aligent/migrate-secrets-pipe:latest
              variables:
                GITHUB_TOKEN: $GITHUB_TOKEN
                GITHUB_REPO: 'myorg/my-app'
                SECRET_NAMES: 'NPM_TOKEN,DOCKER_PASSWORD,SLACK_WEBHOOK'
                NPM_TOKEN: $NPM_TOKEN
                DOCKER_PASSWORD: $DOCKER_PASSWORD
                SLACK_WEBHOOK: $SLACK_WEBHOOK

      # Step 2: Migrate staging environment secrets
      - step:
          name: Migrate Staging Secrets
          deployment: staging
          script:
            - pipe: aligent/migrate-secrets-pipe:latest
              variables:
                ENVIRONMENT: 'staging'
                GITHUB_TOKEN: $GITHUB_TOKEN
                GITHUB_REPO: 'myorg/my-app'
                SECRET_NAMES: 'DATABASE_URL,API_KEY,REDIS_URL'
                DATABASE_URL: $DATABASE_URL
                API_KEY: $API_KEY
                REDIS_URL: $REDIS_URL
      # Step 3: Migrate production environment secrets
      - step:
          name: Migrate Production Secrets
          deployment: production
          script:
            - pipe: aligent/migrate-secrets-pipe:latest
              variables:
                ENVIRONMENT: 'production'
                GITHUB_TOKEN: $GITHUB_TOKEN
                GITHUB_REPO: 'myorg/my-app'
                SECRET_NAMES: 'DATABASE_URL,API_KEY,REDIS_URL'
                DATABASE_URL: $DATABASE_URL
                API_KEY: $API_KEY
                REDIS_URL: $REDIS_URL
```

## Troubleshooting

### Secret not found in Bitbucket

**Error**: `Secret 'XXX' not found in Bitbucket pipeline variables`

**Solution**: Ensure the secret is defined in your Bitbucket repository settings under:
- Repository Settings → Repository variables (for repo-level secrets)
- Repository Settings → Deployments → [Environment] → Variables (for environment secrets)

### Failed to set secret in GitHub

**Error**: `Failed to set repository/environment secret: XXX`

**Solutions**:
- Verify your `GITHUB_TOKEN` has the required scopes
- Check that the `GITHUB_REPO` format is correct (`owner/repo`)
- Ensure the GitHub environment exists (if using `ENVIRONMENT` parameter)

### Permission denied

**Solution**: Ensure your GitHub token has `repo` and `admin:repo_hook` permissions

## Development

To build the Docker image locally:

```bash
docker build -t migrate-secrets-pipe:latest .
```

To test locally (requires environment variables set):

```bash
docker run --rm \
  -e GITHUB_TOKEN="your-token" \
  -e GITHUB_REPO="owner/repo" \
  -e SECRET_NAMES="SECRET1,SECRET2" \
  -e SECRET1="value1" \
  -e SECRET2="value2" \
  migrate-secrets-pipe:latest
```

## License

MIT
