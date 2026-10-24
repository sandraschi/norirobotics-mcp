# Per-repo fleet start config for norirobotics-mcp
@{
    Name         = 'norirobotics-mcp'
    BackendPort  = 11970
    FrontendPort = 11971
    HealthPath   = '/health'
    WebRoot      = 'web_sota'
    Backend = @{
        Kind = 'module-serve'
        Module = 'norirobotics_mcp'
    }
    Frontend = @{
        Kind = 'vite-npm'
        PortEnvVar = 'VITE_PORT'
    }
}
