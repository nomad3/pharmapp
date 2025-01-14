# Comparador de Medicamentos

![Logo](https://via.placeholder.com/150)

**Comparador de Medicamentos** es una aplicación web de demostración que permite a los usuarios comparar precios de distintos medicamentos en farmacias cercanas. La aplicación está desarrollada con **React** para el frontend, **FastAPI** para el backend y utiliza **Docker** para la contenedorización y orquestación de servicios.

## Tabla de Contenidos

1. [Características](#características)
2. [Tecnologías Utilizadas](#tecnologías-utilizadas)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Requisitos Previos](#requisitos-previos)
5. [Instalación](#instalación)
    - [Clonar el Repositorio](#clonar-el-repositorio)
    - [Configuración de Docker](#configuración-de-docker)
6. [Uso](#uso)
    - [Iniciar la Aplicación](#iniciar-la-aplicación)
    - [Acceder a la Aplicación](#acceder-a-la-aplicación)
7. [API Endpoints](#api-endpoints)
8. [Frontend](#frontend)
    - [Estructura de Directorios](#estructura-de-directorios)
    - [Componentes Principales](#componentes-principales)
9. [Troubleshooting](#troubleshooting)
    - [Error de Dependencia de NPM](#error-de-dependencia-de-npm)
10. [Próximos Pasos](#próximos-pasos)
11. [Recursos Adicionales](#recursos-adicionales)
12. [Contribuciones](#contribuciones)
13. [Licencia](#licencia)
14. [Contacto](#contacto)

---

## Características

- **Listado de Medicamentos**: Muestra una lista de medicamentos disponibles con sus descripciones.
- **Comparación de Precios**: Permite a los usuarios comparar los precios de medicamentos en diferentes farmacias.
- **Geolocalización**: (Planificado) Muestra las farmacias cercanas utilizando mapas.
- **Contenedorización**: Utiliza Docker para facilitar el despliegue y la escalabilidad.

## Tecnologías Utilizadas

- **Frontend**:
  - [React](https://reactjs.org/)
  - [Axios](https://axios-http.com/)
  - [Nginx](https://www.nginx.com/)
- **Backend**:
  - [FastAPI](https://fastapi.tiangolo.com/)
  - [Uvicorn](https://www.uvicorn.org/)
  - [Pydantic](https://pydantic-docs.helpmanual.io/)
- **Contenedorización**:
  - [Docker](https://www.docker.com/)
  - [Docker Compose](https://docs.docker.com/compose/)
  
## Estructura del Proyecto

```
comparador_medicamentos/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── models.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.css
│   │   ├── App.js
│   │   └── index.js
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
└── docker-compose.yml
```

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalados los siguientes componentes en tu sistema:

- **Docker**: [Descargar e instalar Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: Generalmente viene incluido con Docker Desktop.
- **Node.js y npm**: [Descargar e instalar Node.js](https://nodejs.org/)
- **Python 3.8+**: [Descargar e instalar Python](https://www.python.org/downloads/)
- **Git**: [Descargar e instalar Git](https://git-scm.com/downloads)

## Instalación

### Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/comparador_medicamentos.git
cd comparador_medicamentos
```

### Configuración de Docker

Asegúrate de que Docker esté corriendo en tu sistema. Luego, construye y levanta los contenedores utilizando Docker Compose.

```bash
docker-compose up --build
```

Este comando construirá las imágenes de Docker para el frontend y el backend, y levantará los contenedores conectados a una red interna.

## Uso

### Iniciar la Aplicación

Ejecuta el siguiente comando desde el directorio raíz del proyecto para iniciar los servicios:

```bash
docker-compose up --build
```

### Acceder a la Aplicación

- **Frontend (React)**: Abre [http://localhost:3000](http://localhost:3000) en tu navegador.
- **Backend (FastAPI)**: Accede a [http://localhost:8000/medicamentos](http://localhost:8000/medicamentos) para ver la lista de medicamentos.

## API Endpoints

La API de **FastAPI** proporciona los siguientes endpoints básicos:

- **GET /medicamentos**: Retorna una lista de medicamentos.
- **GET /farmacias**: Retorna una lista de farmacias.
- **GET /precios**: Retorna los precios de un medicamento en una farmacia específica.

### Ejemplos

- Obtener medicamentos:
  ```
  GET http://localhost:8000/medicamentos
  ```

- Obtener farmacias:
  ```
  GET http://localhost:8000/farmacias
  ```

- Obtener precio de un medicamento en una farmacia:
  ```
  GET http://localhost:8000/precios?medicamento_id=1&farmacia_id=2
  ```

## Frontend

### Estructura de Directorios

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── App.css
│   ├── App.js
│   └── index.js
├── Dockerfile
├── nginx.conf
└── package.json
```

### Componentes Principales

- **App.js**: Componente principal que obtiene y muestra la lista de medicamentos.
- **App.css**: Estilos básicos para la aplicación.

## Troubleshooting

### Error de Dependencia de NPM

**Mensaje de Error:**
```
npm ERR! Could not resolve dependency:
npm ERR! peer react@"^18.0.0" from @testing-library/react@13.4.0
```

**Causa:**
Este error ocurre cuando la versión de React instalada no cumple con la versión requerida por `@testing-library/react`.

**Solución:**

1. **Verificar la Versión de React:**

   Asegúrate de que tu proyecto React esté utilizando React 18 o superior.

   ```bash
   npm list react
   ```

2. **Actualizar React:**

   Si estás usando una versión inferior a la requerida, actualiza React y React DOM.

   ```bash
   npm install react@^18.0.0 react-dom@^18.0.0
   ```

3. **Eliminar `node_modules` y Reinstalar Dependencias:**

   A veces, limpiar las dependencias y reinstalarlas puede resolver conflictos.

   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **Verificar las Dependencias en `package.json`:**

   Asegúrate de que las versiones de React en tu `package.json` sean compatibles con las versiones requeridas por otras librerías.

   ```json
   {
     "dependencies": {
       "react": "^18.0.0",
       "react-dom": "^18.0.0",
       // otras dependencias
     },
     "devDependencies": {
       "@testing-library/react": "^13.4.0",
       // otras dependencias de desarrollo
     }
   }
   ```

5. **Forzar la Resolución de Dependencias:**

   Si persiste el problema, puedes intentar forzar la resolución utilizando `--legacy-peer-deps` (no recomendado para producción).

   ```bash
   npm install --legacy-peer-deps
   ```

**Nota:** Es importante mantener las versiones de las dependencias actualizadas para evitar conflictos y asegurar la compatibilidad.

## Próximos Pasos

Para avanzar hacia un MVP funcional, considera las siguientes mejoras:

- **Autenticación de Usuarios**: Implementar registro e inicio de sesión.
- **Base de Datos Persistente**: Integrar una base de datos como PostgreSQL o MongoDB para almacenar datos dinámicamente.
- **Geolocalización**: Integrar mapas para mostrar farmacias cercanas basadas en la ubicación del usuario.
- **UI/UX Mejorada**: Mejorar la interfaz de usuario para una experiencia más amigable.
- **Gestión de Precios en Tiempo Real**: Implementar actualizaciones dinámicas de precios de medicamentos.

## Recursos Adicionales

- **FastAPI**
  - [Documentación Oficial](https://fastapi.tiangolo.com/)
  - [Tutoriales y Ejemplos](https://fastapi.tiangolo.com/tutorial/)
  
- **React**
  - [Documentación Oficial](https://reactjs.org/docs/getting-started.html)
  - [Tutoriales de Create React App](https://create-react-app.dev/docs/getting-started/)
  
- **Docker**
  - [Documentación Oficial](https://docs.docker.com/)
  - [Guía de Docker Compose](https://docs.docker.com/compose/)
  
- **Integración de FastAPI y React**
  - [Tutorial: Crear API con FastAPI y Consumir con React](https://testdriven.io/blog/fastapi-react/)
  
- **Buenas Prácticas**
  - [Organización de Proyectos con Docker](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
  - [Seguridad en Docker](https://docs.docker.com/engine/security/)

## Contribuciones

¡Las contribuciones son bienvenidas! Si deseas mejorar este proyecto, sigue estos pasos:

1. **Fork el Repositorio**
2. **Crear una Rama de Feature**
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```
3. **Commit tus Cambios**
   ```bash
   git commit -m "Añadir nueva funcionalidad"
   ```
4. **Push a la Rama**
   ```bash
   git push origin feature/nueva-funcionalidad
   ```
5. **Abrir un Pull Request**

Por favor, asegúrate de seguir las buenas prácticas de codificación y de documentar tus cambios de manera clara.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Para consultas o más información, contacta a:

- **Nombre**: Juan Pérez
- **Correo Electrónico**: juan.perez@example.com
- **LinkedIn**: [linkedin.com/in/juanperez](https://www.linkedin.com/in/juanperez)

---

¡Gracias por utilizar **Comparador de Medicamentos**! Esperamos que esta aplicación te sea de gran ayuda para encontrar los mejores precios en medicamentos cerca de ti.

