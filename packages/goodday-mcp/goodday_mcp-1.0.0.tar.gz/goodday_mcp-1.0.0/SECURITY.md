# Security Policy

## Supported Versions

We actively support the following versions of goodday-mcp:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in goodday-mcp, please report it by:

1. **Do NOT** create a public GitHub issue
2. Email the maintainers directly at: security@example.com
3. Include a detailed description of the vulnerability
4. Provide steps to reproduce if possible
5. Include any potential impact assessment

## Response Process

1. **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
2. **Investigation**: We will investigate and validate the reported vulnerability
3. **Fix Development**: If confirmed, we will develop and test a fix
4. **Release**: We will release a patched version as soon as possible
5. **Disclosure**: We will publicly disclose the vulnerability after the fix is released

## Security Considerations

### API Token Security
- **Never commit API tokens** to version control
- Use environment variables for token storage
- Rotate API tokens regularly
- Limit API token permissions to minimum required

### Network Security
- All API communications use HTTPS
- Validate all API responses
- Implement proper timeout handling

### Input Validation
- All user inputs are validated before API calls
- SQL injection protection (not applicable for this REST API client)
- XSS protection in data formatting

## Best Practices

1. **Keep Dependencies Updated**: Regularly update dependencies
2. **Monitor for Vulnerabilities**: Use tools like `pip-audit` to scan for known vulnerabilities
3. **Secure Configuration**: Follow the configuration guidelines in README.md
4. **Access Control**: Limit access to GoodDay API tokens

## Dependency Security

This project uses:
- `httpx` for HTTP requests (actively maintained, security-focused)
- `mcp` for Model Context Protocol (official implementation)

We monitor these dependencies for security updates and will update promptly when security patches are available.
