# Editor de texto Notepad++: complementos de accesibilidad #
* Autor: PaulBer19
* URL: paulber19@laposte.net
* Descargar:
	* [versión estable][1]
	* [versión de desarrollo][2]
* Compatibilidad:
	* Versión mínima de NVDA requerida: 2020.4
	* Última versión de NVDA probada: 2022.3


# Características #

Este complemento tiene como objetivo mejorar la accesibilidad del editor de texto Notepad++ y añadir características para facilitar la edición de archivos utilizados en el lenguaje Python y los archivos escritos en lenguaje markdown.

Este complemento vuelve a tomar la mayoria de los suplementos proporcionados por el complemento NVDA_notepadPlusPlus creado por Derek Riemer y Tuukka Ojala, luego modificado por Robert Hänggi y Andre9642 <https://github.com/derekriemer/nvda-notepadPlusPlus>.

A saber:

* verbalización del resultado de la órden "control+b" que permite moverse al delimitador simétrico,
* verbalización  del desplazamiento  al siguiente o anterior marcador mediante "F2" o "mayúscula+f2",
* informar de línea demasiado larga,
* accesibilidad al autocompletado,
* accesibilidad a la búsqueda incremental,
* Apoyo a la función de busqueda anterior / siguiente.


Para los archivos de Python, el complemento proporciona:

* desplazamiento a la siguiente clase o método,
* importación del código de la ventana de edición.


Para los archivos Markdown o txt2tags:

* vista previa del resultado de la conversión en HTML en el búfer virtual de NVDA o en el navegador predeterminado,
* añadido el Modo Exploración para encabezados, enlaces, citas.



Y los otros suplementos:

* Anuncio del número y la sangría de cada línea,
* scripts para establecer la sangría,
* Verbalización del desplazamiento del foco mediante la tecla "inicio",
* Comparación del texto seleccionado con el del portapapeles,
* ir a la siguiente línea que termina al menos con una tabulación o un espacio,
* disposición del anuncio del nombre de los documentos:
	* anuncio reducido de la ruta de archivos,
	* anuncio del nombre del archivo antes de su ruta,
	* no verbalización de las barras inversas en la ruta.


# Compatibilidad #
Este complemento ha sido probado con  Notepad++ versión 7.71.


# Restricciones #
Este complemento usa e intercepta los atajos de Notepad++ configurados por defecto. Por lo tanto, se recomienda encarecidamente, por su correcto funcionamiento, no modificar estos atajos.


[1]: https://github.com/paulber007/AllMyNVDAAddons/raw/notepadPlusPlusAccessEnhancement/notepadPlusPlusAccessEnhancement/notepadPlusPlusAccessEnhancement-2.2.1.nvda-addon
[2]: https://github.com/paulber007/AllMyNVDAAddons/tree/master/notepadPlusPlusAccessEnhancement/dev
