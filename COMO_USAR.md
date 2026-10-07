# Cómo usarlo

1. Creá un repo **público** que se llame igual que tu usuario de GitHub (si ya lo tenés, usá ese).
2. Subí todo el contenido de esta carpeta a la rama principal, incluida la carpeta oculta `.github`.
3. Listo: al subirlo corre la Action "Actualizar perfil", que completa tu usuario y tus stats y genera la viborita. Después se actualiza sola todos los días.

## Personalizar

- **`perfil.json`**: tus datos. Cada campo es `["Etiqueta", "valor"]`; podés agregar, sacar o reordenar.
  - `"usuario"`: vacío = usa el dueño del repo.
  - `"idioma"`: `"en"` o `"es"`; cambia los textos automáticos (Uptime, Followers, etc.).
  - `"minusculas"`: `true` pasa todo el texto a minúsculas; `false` lo deja como lo escribiste.
  - `"{uptime}"` se reemplaza por tu edad si completás `"nacimiento": "AAAA-MM-DD"`; si lo dejás vacío, por la antigüedad de tu cuenta.
  - `"{lenguajes}"` se reemplaza por tus 4 lenguajes más usados en tus repos públicos. `lenguajes_ignorar` saca los que no quieras contar. Si preferís una lista fija, escribila en lugar de `"{lenguajes}"`.
- **`ascii.txt`**: el dibujo de la izquierda. Ahora es ゆめ ("yume", "sueño") escrito en vertical. Podés reemplazarlo por cualquier arte ASCII.
  - `"ascii_fuente"` es el tamaño de letra del dibujo: con 10 entran unas 36 filas, con 14 unas 22, con 8 unas 47.
  - Los caracteres `.,-~:;=!*#$@` se pintan en degradé verde; con `"ascii_degrade": false` va todo de un color.
- **Colores**: están en `TEMAS`, al principio de `generar.py`.

Para probar en tu compu: `python generar.py --demo` (usa números de ejemplo).

## Opcional: contar repos y commits privados

Por defecto solo se cuenta lo público. Para sumar lo privado, creá un token personal con permiso de lectura y guardalo en el repo como secret `PERFIL_TOKEN`.

Cuando termines podés borrar este archivo.
