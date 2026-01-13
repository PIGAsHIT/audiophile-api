terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.1"
    }
  }
}

provider "docker" {}

# 1. 新增：建立專用網路
# 這樣 Redis 和 Postgres 才能互相溝通
resource "docker_network" "audiophile_net" {
  name = "audiophile_network"
}

# --- Redis 區塊 (有小修改) ---

resource "docker_image" "redis" {
  name         = "redis:latest"
  keep_locally = false
}

resource "docker_container" "redis" {
  image = docker_image.redis.image_id
  name  = "terraform-redis"
  
  ports {
    internal = 6379
    external = 6379
  }

  # 把 Redis 加入網路
  networks_advanced {
    name = docker_network.audiophile_net.name
  }
}

# --- PostgreSQL 區塊 (新增) ---

resource "docker_image" "postgres" {
  name         = "postgres:15"
  keep_locally = false
}

resource "docker_container" "postgres" {
  image = docker_image.postgres.image_id
  name  = "terraform-postgres"
  
  # 設定環境變數 (跟你的 .env 保持一致)
  env = [
    "POSTGRES_USER=user",
    "POSTGRES_PASSWORD=password",
    "POSTGRES_DB=audiophile"
  ]
  
  ports {
    internal = 5432
    external = 5432
  }

  # 把 Postgres 加入網路
  networks_advanced {
    name = docker_network.audiophile_net.name
  }
  
  # 掛載 Volume (讓資料庫重開機資料還在)
  volumes {
    host_path      = abspath("${path.cwd}/pgdata") # 會在當前目錄建立資料夾
    container_path = "/var/lib/postgresql/data"
  }
}

# --- MongoDB 區塊 (Log 專用) ---

resource "docker_image" "mongo" {
  name         = "mongo:latest"
  keep_locally = false
}

resource "docker_container" "mongo" {
  image = docker_image.mongo.image_id
  name  = "terraform-mongo"
  
  # 設定帳密 (與 .env 對應)
  env = [
    "MONGO_INITDB_ROOT_USERNAME=admin",
    "MONGO_INITDB_ROOT_PASSWORD=password"
  ]
  
  ports {
    internal = 27017
    external = 27017
  }

  # 加入同一個網路，這樣 App 才能連到它
  networks_advanced {
    name = docker_network.audiophile_net.name
  }
  
  # 掛載 Volume (保留 Log 資料)
  volumes {
    host_path      = abspath("${path.cwd}/mongodata")
    container_path = "/data/db"
  }
}