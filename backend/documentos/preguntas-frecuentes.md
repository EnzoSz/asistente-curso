# Preguntas frecuentes del curso (documento de ejemplo)

Este documento es un ejemplo armado para las prácticas del Módulo 3. El docente puede completarlo o corregirlo con la información real de la cohorte.

## ¿Dónde encuentro el material de cada clase?

En el aula virtual, dentro del módulo correspondiente. Por cada clase síncrona se publican la presentación, la grabación y una carpeta comprimida con la práctica. El material se sube dentro de las 24 horas posteriores a la clase.

## ¿Conviene descargar las grabaciones?

No hace falta. Se recomienda reproducirlas directamente desde Google Drive, sin descargarlas, porque los archivos son pesados.

## ¿Cuántas veces puedo hacer cada test?

Cada test semanal tiene 10 preguntas de alternativa múltiple y admite hasta 3 intentos. Se toma la nota más alta de todos los intentos.

## ¿Los tests cuentan para la nota del módulo?

No. Los tests son formativos: sirven para verificar el avance de cada semana. La nota del módulo sale en un 100 % del assignment.

## ¿Qué cuentas necesito para el Módulo 3?

Dos cuentas gratuitas. La de NVIDIA (build.nvidia.com), la misma del Módulo 2, para los modelos Nemotron. Y una cuenta de LangSmith (smith.langchain.com) en el plan Developer, que es gratuito y alcanza para trazas, datasets y evaluaciones.

## ¿Tengo que pagar para desplegar el agente?

No para las prácticas. En clase el agente se despliega con el servidor local de LangGraph (langgraph dev), que es el mismo Agent Server que usa LangSmith Deployment. El despliegue en la nube de LangSmith requiere el plan Plus, que es pago. Qué evidencias de despliegue se aceptan para el assignment lo confirma el docente.

## ¿Puedo usar la misma clave de NVIDIA del Módulo 2?

Sí. La clave NVIDIA_API_KEY es la misma para todas las prácticas. Se copia en el archivo .env de cada carpeta, junto con la clave de LangSmith.

## ¿Qué hago si uv no funciona después de instalarlo?

Casi siempre es un problema de PATH. Hay que cerrar la terminal y abrirla de nuevo. Si se usa VS Code, conviene cerrarlo del todo y volver a abrirlo, o abrirlo desde una terminal externa con el comando code punto.

## ¿El assignment del Módulo 3 lleva código?

Sí. A diferencia del Módulo 2, el assignment del Módulo 3 pide implementar y desplegar un agente, y presentar evidencias de LangSmith: trazas, evaluaciones y métricas. Se entrega como un informe técnico con capturas.

## ¿Cuánto tiempo se guardan las trazas en LangSmith?

En el plan gratuito, las trazas base se guardan 14 días. Conviene sacar las capturas para el informe apenas se generan las ejecuciones.
