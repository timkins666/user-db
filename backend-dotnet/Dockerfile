# ---------- Base for build/development ----------
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS base
WORKDIR /src

# Copy solution and project files first (better caching)
COPY backend-dotnet.sln ./
COPY api/*.csproj ./api/
# remove this xxx
COPY api-tests/*.csproj ./api-tests/
# (repeat COPY for other projects if you have them)

RUN dotnet restore backend-dotnet.sln

# Copy everything else
COPY . .

# ---------- Development stage (hot reload) ----------
FROM base AS dev
WORKDIR /src/api
# Entrypoint for hot reload
ENTRYPOINT ["dotnet", "watch", "run", "--no-launch-profile", "--urls", "http://0.0.0.0:5000", "--hot-reload", "--restart"]

# ---------- Build + publish ----------
FROM base AS build
WORKDIR /src/api
RUN dotnet build -c Release -o /app/build
RUN dotnet publish -c Release -o /app/publish /p:UseAppHost=false

# ---------- Production runtime ----------
FROM mcr.microsoft.com/dotnet/aspnet:9.0 AS final
WORKDIR /app
COPY --from=build /app/publish .
ENTRYPOINT ["dotnet", "api.dll"]
