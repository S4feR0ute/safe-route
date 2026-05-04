# SafeRoute

## Descripción

SafeRoute Lima es una aplicación web orientada a Smart City y servicios públicos que permite a los ciudadanos de Lima Metropolitana consultar rutas peatonales optimizadas por seguridad. El sistema integra datos públicos de criminalidad agregados por distrito (SIDPOL) con datos geoespaciales de OpenStreetMap (grafo de calles y contexto urbano) para calcular un índice de riesgo compuesto por segmento de calle y sugerir la ruta más segura entre dos puntos.

## Objetivo

Brindar a los usuarios una herramienta que les permita desplazarse de manera más segura dentro de la ciudad mediante el uso de tecnología de geolocalización.

## Estructura del proyecto

El proyecto está dividido en:

 **frontend/**: Aplicación web desarrollada con React y Vite
 **backend/**: Lógica del servidor (en desarrollo)
 **docs/**: Documentación del proyecto
 **Casos de prueba**: Archivos PDF con pruebas diseñadas para validar el sistema

## Tecnologías utilizadas

 React
 Vite
 React Router DOM
 Leaflet
 React Leaflet
 ESLint

## Instalación y ejecución

### 1. Clonar el repositorio


git clone https://github.com/S4feR0ute/safe-route.git
cd safe-route


### 2. Ejecutar el frontend

cd frontend
npm install
npm run dev


Luego abrir en el navegador:


http://localhost:5173


## Testing

Se diseñaron casos de prueba basados en los requisitos funcionales del sistema para validar el comportamiento de la aplicación.

Las pruebas incluyen:

 Validación de entradas del usuario
 Verificación de navegación entre vistas
 Comprobación del funcionamiento del mapa interactivo
 Evaluación del flujo de búsqueda de rutas

Los casos de prueba se encuentran documentados en archivos PDF dentro del repositorio.

## Equipo

 Pedro Vargas Alfaro – BA(Business Analyst)
 Jharvy Cadillo Tarazona - Dev Backend
 Luis Alanya Campos – Dev Frontend
 Anngie Salazar Alvarez – QA(Quality Assurance)

## Estado del proyecto

Proyecto en desarrollo – Sprint 1

## Documentación adicional

Consultar la carpeta **docs/** para más detalles del proyecto.


