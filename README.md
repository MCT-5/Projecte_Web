# Deal Tracker - Projecte Web 2025/26

Plataforma web de rastreo y comparativa de precios de videojuegos desarrollada para la asignatura Projecte Web. Este proyecto centraliza y analiza ofertas de múltiples tiendas para ayudar a los usuarios a encontrar el mejor precio de mercado.

##  Requisitos Previos

Este proyecto se ha desarrollado siguiendo las directrices de una aplicación **12-factor**. Para ejecutarlo de forma orquestada mediante contenedores, necesitas tener instalado:
* [Docker Desktop](https://www.docker.com/products/docker-desktop)
* [Git](https://git-scm.com/)

##  Instrucciones de Despliegue

Sigue estos pasos detallados para levantar la aplicación en tu entorno local:

**1. Clonar el repositorio**
\`\`\`bash
git clone <TU_URL_DE_GITHUB_AQUI>
cd <NOMBRE_DE_TU_CARPETA>
\`\`\`

**2. Configurar las Variables de Entorno (.env)**
Para aislar la configuración del código base, crea un archivo llamado `.env` en la raíz del proyecto y añade las siguientes variables:
\`\`\`env
DEBUG=True
SECRET_KEY=escribe-una-clave-segura-aqui
RAWG_API_KEY=tu_clave_de_rawg
ITAD_API_KEY=tu_clave_de_itad
\`\`\`

**3. Levantar los contenedores con Docker Compose**
Ejecuta el siguiente comando para construir la imagen y levantar el servidor web:
\`\`\`bash
docker-compose up --build
\`\`\`
*(El servidor estará disponible en http://localhost:8000)*

**4. Inicializar la Base de Datos y Crear Superusuario**
En una nueva terminal, ejecuta las migraciones para crear las tablas del modelo de datos e inicializa la interfaz de administrador:
\`\`\`bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
\`\`\`

---

## Población de la Base de Datos (Automatización)

Para poblar nuestra base de datos automatizada y no depender únicamente de la entrada manual, el proyecto incluye comandos personalizados (Management Commands) en Django que consumen APIs externas.

Para ejecutar estos scripts dentro del contenedor, utiliza los siguientes comandos:

* **Descargar catálogo de juegos (RAWG API):**
  Extrae los títulos oficiales, géneros y carátulas.
  \`\`\`bash
  docker-compose exec web python manage.py fetch_rawg_games --start-page 1 --end-page 2
  \`\`\`

* **Buscar ofertas en mercado digital (IsThereAnyDeal API):**
  Rellena la tabla con ofertas digitales obteniendo el precio actual y la tienda.
  \`\`\`bash
  docker-compose exec web python manage.py fetch_itad_prices
  \`\`\`
  
* **Buscar ofertas (CheapShark API - Alternativa):**
  \`\`\`bash
  docker-compose exec web python manage.py fetch_prices
  \`\`\`

---

## Explicación Técnica y Decisiones de Diseño (Code Walkthrough)

A nivel de código, se han resuelto varios retos técnicos de integración para garantizar la estabilidad del sistema y la coherencia de los datos entre distintas plataformas.

### 1. Normalización de Cadenas (Regex) en `fetch_itad_prices`
**El Reto:** Los nombres de los videojuegos varían entre la base de datos de RAWG y la de IsThereAnyDeal. Por ejemplo, buscar un título literal puede devolver un error de "no encontrado" si una API incluye la coletilla "GOTY Edition" y la otra no.
**La Solución:** Antes de consultar la API de ofertas, el script ejecuta la función `clean_game_title()`. Esta utiliza Expresiones Regulares (`re`) para:
* Purgar símbolos registrados (™, ®).
* Sustituir caracteres especiales (cambia "&" por "and").
* Eliminar subtítulos comerciales cortando la cadena (`.split(' edition')[0]`).
* Suprimir puntuación problemática (`re.sub(r'[:\'\-,.!]', '', t)`).
Esto maximiza exponencialmente el *Hit Rate* de coincidencias en la API de destino.

### 2. Algoritmo de Rate Limiting Matemático (`fetch_prices` / `fetch_itad_prices`)
**El Reto:** Consultar las ofertas de cientos de juegos en un bucle cerrado provoca bloqueos por exceso de peticiones (*HTTP 429 Too Many Requests*) por parte de los proveedores de las APIs.
**La Solución:** Se ha diseñado un tamaño de lote dinámico (*dynamic batch size*) basado en una función logarítmica. El sistema evalúa el volumen total de juegos registrados en la base de datos y calcula un límite seguro antes de forzar una pausa en el hilo de ejecución (`time.sleep(120)`).

La fórmula matemática implementada en Python mediante la librería `math` es:

$$B = \frac{x}{8.5 \cdot \log_{10}(x)}$$

Donde $x$ es el total de juegos en la base de datos y $B$ es el tamaño del lote. Esto asegura que la aplicación escale eficientemente, protegiendo las credenciales de la API independientemente del tamaño del catálogo.

### 3. Idempotencia y Evolución Histórica
* **Prevención de duplicados:** Se utiliza intensivamente el método `get_or_create()` y `update_or_create()` del ORM de Django. Esto permite que los comandos se ejecuten de forma recurrente sin duplicar juegos ni tiendas en la base de datos.
* **Trazabilidad de Precios:** Cada vez que se detecta o actualiza una oferta en `PRICE_LISTING`, el script ejecuta simultáneamente un registro en `PRICE_HISTORY`. Esto genera un registro temporal inmutable que da soporte a la funcionalidad principal de visualización de evolución de precios a lo largo del tiempo.
