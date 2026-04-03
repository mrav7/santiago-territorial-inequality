# Resumen de homologacion comunal

## Base maestra validada
- Filas esperadas: 32; filas observadas: 32.
- `codigo_comuna` unico: si.
- `nombre_comuna` unico: si.
- Provincia observada: SANTIAGO.
- Region observada: METROPOLITANA DE SANTIAGO.
- Criterio operativo: La llave principal del proyecto es `codigo_comuna`. `nombre_comuna` se usa solo como apoyo descriptivo y de verificacion; no deben hacerse joins futuros por nombre crudo.

## Resultados por fuente
- Fuente A: 52 codigos validos; 32 dentro del universo final y 20 fuera de alcance.
  Coincidencias exactas=26; por normalizacion=6; por homologacion manual=0; manuales pendientes=0.
- Fuente B: 52 codigos validos; 32 dentro del universo final y 20 fuera de alcance.
  Coincidencias exactas=26; por normalizacion=6; por homologacion manual=0; manuales pendientes=0.
- Fuente C: 345 codigos validos; 32 dentro del universo final y 313 fuera de alcance.
  Coincidencias exactas=0; por normalizacion=32; por homologacion manual=0; manuales pendientes=0.
- Fuente D: 347 codigos validos; 32 dentro del universo final y 315 fuera de alcance.
  Coincidencias exactas=0; por normalizacion=32; por homologacion manual=0; manuales pendientes=0.

## Recomendacion operativa
- Todos los merges futuros deben hacerse por `codigo_comuna`.
- `nombre_comuna` debe mantenerse solo para verificaciones, trazabilidad y presentacion.
- Los registros `fuera_de_alcance` no deben entrar al dataset final de la Provincia de Santiago.
- No quedan casos con homologacion manual pendiente dentro del universo final.
