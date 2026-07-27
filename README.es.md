# flet-mvc

Modelos de dominio reactivos avanzados para Flet, con una estructura MVC
opcional.

[English](https://github.com/o0Adrian/flet-mvc/blob/master/README.md) ·
[Español](https://github.com/o0Adrian/flet-mvc/blob/master/README.es.md)

> La próxima versión 1.0 de flet-mvc está dirigida a Flet `>=0.86.3,<0.87` y
> Python 3.10 o posterior. El límite superior es intencional: cada nueva
> versión menor de Flet se audita antes de ampliar el rango.

flet-mvc le da al modelo de dominio un poco más de estructura que un
observable sencillo:

- `@data` declara estado modificable;
- `@computed` declara estado derivado de solo lectura;
- las dependencias forman un grafo determinista;
- incluye lotes, snapshots, suscripciones y bindings con controles;
- `FletModel` es un `ft.Observable` nativo y funciona con `@ft.component`.

Puedes usar MVC cuando separar modelos, vistas y controladores facilite el
mantenimiento del proyecto. No es obligatorio. Flet sigue siendo responsable
de los controles, `ft.View`, `ft.Router`, los diálogos, la navegación, el
renderizado y el ciclo de vida de la aplicación.

## Elige una ruta

- Para construir algo ahora, sigue el [Inicio rápido](#inicio-rápido).
- Para aprender la API de estado, lee [Estado del modelo](#estado-del-modelo).
- Para usar MVC con clases, abre
  [Estructura MVC opcional](#estructura-mvc-opcional).
- Para migrar código antiguo, usa la
  [guía de migración](https://github.com/o0Adrian/flet-mvc/blob/master/MIGRATION.md).
- Para conectar un control, consulta la
  [matriz de controles](https://github.com/o0Adrian/flet-mvc/blob/master/docs/CONTROL_COMPATIBILITY.md).
- Para revisar la actualización de Flet, lee la
  [auditoría de versiones](https://github.com/o0Adrian/flet-mvc/blob/master/docs/FLET_RELEASE_AUDIT.md).

## Instalación

Crea y activa un entorno virtual:

```bash
python -m venv .venv
```

En macOS o Linux:

```bash
source .venv/bin/activate
```

En Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Instala flet-mvc:

```bash
python -m pip install --upgrade pip
python -m pip install "flet-mvc>=1.0,<2"
```

El paquete instala automáticamente el rango de Flet que ha sido probado.

| flet-mvc | Flet | Python | Estado |
|---|---|---|---|
| 1.0.x | `>=0.86.3,<0.87` | 3.10–3.14 | Objetivo actual |
| 0.1.5 | 0.9.0 en la práctica | Histórico | Legado |

## Inicio rápido

Esta primera aplicación usa un modelo de flet-mvc directamente desde la UI
declarativa de Flet. Todavía no necesitas entender un controlador ni una
clase de vista personalizada.

Crea `app.py`:

```python
import flet as ft

from flet_mvc import FletModel, computed, data


class CounterModel(FletModel):
    @data
    def count(self) -> int:
        return 0

    @computed
    def message(self) -> str:
        return f"Count: {self.count.value}"


@ft.component
def Counter(model: CounterModel) -> ft.Control:
    return ft.Column(
        controls=[
            ft.Text(model.message.value, size=28),
            ft.Button(
                content="Add one",
                icon=ft.Icons.ADD,
                on_click=lambda: model.count.update(lambda value: value + 1),
            ),
        ]
    )


def main(page: ft.Page) -> None:
    page.title = "Reactive counter"
    page.render(Counter, CounterModel())


if __name__ == "__main__":
    ft.run(main)
```

Ejecútala:

```bash
python app.py
```

Cada clic sigue un flujo predecible:

```text
Evento del botón
  → count.update(...)
  → count cambia
  → message se recalcula
  → Flet observa el modelo
  → Counter renderiza los valores nuevos
```

Este ejemplo declarativo no necesita `page.update()`.

## Estado del modelo

### Estado modificable con `@data`

El método decorado proporciona el valor predeterminado. Cada instancia del
modelo tiene datapoints independientes.

```python
from flet_mvc import FletModel, data


class OrderModel(FletModel):
    @data
    def quantity(self) -> int:
        return 1

    @data
    def unit_price(self) -> float:
        return 9.50


first = OrderModel()
second = OrderModel(quantity=3)

assert first.quantity.value == 1
assert second.quantity.value == 3

first.quantity.set(2)
first.quantity.update(lambda quantity: quantity + 1)
assert first.quantity.value == 3

first.quantity.reset()
assert first.quantity.value == 1
```

Usa:

- `point.value` para leer;
- `point.set(value)` para reemplazar un valor;
- `point.update(transform)` para obtener el siguiente valor a partir del actual;
- `point.reset()` para volver a evaluar su método `@data`.

No asignes `model.quantity = 2`. El descriptor rechaza la asignación directa
para que ningún cambio evite la propagación.

Los descriptores son genéricos. Un método que devuelve `int` se convierte en
`Datapoint[int]`, así que el verificador de tipos valida `.value`, `set()`,
`update()` y `use_datapoint()` sin anotaciones adicionales.

### Estado derivado con `@computed`

Un datapoint calculado es de solo lectura. flet-mvc registra cuáles datapoints
lee y lo vuelve a calcular cuando cambia alguna dependencia.

```python
from flet_mvc import FletModel, computed, data


class OrderModel(FletModel):
    @data
    def quantity(self) -> int:
        return 1

    @data
    def unit_price(self) -> float:
        return 9.50

    @computed
    def total(self) -> float:
        return self.quantity.value * self.unit_price.value


model = OrderModel()
assert model.total.value == 9.50

model.quantity.set(4)
assert model.total.value == 38.0
```

Llamar `set()`, `update()` o `reset()` sobre `total` produce `TypeError`.
Modifica los datos de los que depende.

Las dependencias pueden cambiar durante la ejecución. Por ejemplo, una
propiedad calculada puede leer `personal_price` en una rama y
`business_price` en otra. El grafo elimina las conexiones obsoletas cuando
cambia la rama activa.

Si una dependencia está oculta detrás de código que no lee el datapoint
durante la evaluación, declárala:

```python
class SearchModel(FletModel):
    @data
    def query(self) -> str:
        return ""

    @computed.depends_on("query")
    def normalized_query(self) -> str:
        return normalize_external_query(self.query.value)
```

`normalize_external_query` representa una función de la aplicación en este
ejemplo. Las dependencias desconocidas y los ciclos fallan con un error de
dependencia específico.

### Reemplaza las colecciones en vez de modificarlas silenciosamente

Usa `update()` para devolver una colección nueva:

```python
from flet_mvc import FletModel, data


class WorkspaceModel(FletModel):
    @data
    def items(self) -> list[dict]:
        return []

    @data
    def filters(self) -> dict:
        return {}


model = WorkspaceModel()
new_item = {"id": 3, "name": "Document"}
model.items.update(lambda items: [*items, new_item])
model.filters.update(lambda filters: {**filters, "active": True})
```

Una modificación interna como `model.items.value.append(new_item)` cambia la
lista de Python sin avisar al grafo de dependencias. Prefiere actualizaciones
de estilo inmutable como la del ejemplo.

### Suscríbete a los cambios

Los suscriptores reciben un `DatapointChange` inmutable. La función devuelta
cancela la suscripción de forma segura, incluso si la llamas más de una vez.

```python
def report(change) -> None:
    print(change.name, change.old_value, change.new_value, change.source)


unsubscribe = model.total.subscribe(report, fire_immediately=True)
model.quantity.set(2)
unsubscribe()
```

Se admiten suscriptores síncronos y asíncronos. Las notificaciones se ejecutan
después de que el grafo de dependencias alcanza un estado consistente.

### Agrupa cambios relacionados

`batch()` retrasa la propagación hasta salir del bloque más externo. Cada
datapoint calculado afectado se evalúa una sola vez con los valores finales.

```python
with model.batch():
    model.quantity.set(2)
    model.unit_price.set(20.0)

assert model.total.value == 40.0
```

Los lotes anidados forman parte de la misma transacción exterior. El
`batch()` más externo es un límite de commit atómico: si una excepción sale
de su cuerpo, o falla un valor calculado o un binding con un control mientras
se estabiliza el grafo, flet-mvc restaura los valores modificables y
calculados, las propiedades de los controles enlazados, las aristas de
dependencia, las colas pendientes y `model.revision`. Los suscriptores de
datapoints y el observable nativo del modelo no reciben notificaciones del
commit fallido.

Este rollback protege el grafo del modelo en memoria; no puede deshacer
efectos externos de tu aplicación en bases de datos, archivos o la red.

### Guarda y restaura el estado del modelo

```python
saved = model.snapshot()

model.quantity.set(99)
model.restore(saved)

assert model.quantity.value == saved["quantity"]
```

Los snapshots son diccionarios superficiales con los valores modificables
de `@data`. Omiten los valores calculados porque al restaurar sus dependencias
se vuelven a crear. `restore(values, strict=False)` ignora claves desconocidas,
lo que resulta útil al cargar datos guardados por una versión anterior. Los
snapshots sirven para persistencia y capturas manuales; `batch()` no necesita
uno para revertir automáticamente un commit fallido.

### Inspecciona el grafo de dependencias

```python
print(model.dependency_graph)
print(model.dependency_dot())
```

`dependency_graph` relaciona cada datapoint con los nombres de sus
dependencias. `dependency_dot()` devuelve Graphviz DOT para depuración o
visualización.

## Usa el modelo con Flet nativo

### Componentes declarativos

`FletModel` hereda de `ft.Observable`. Pasa un modelo a `@ft.component`, lee
los valores de sus datapoints durante el renderizado y deja que Flet programe
el siguiente render. Es el punto de partida recomendado para aplicaciones
declarativas nuevas.

```python
@ft.component
def OrderSummary(model: OrderModel) -> ft.Control:
    return ft.Column(
        controls=[
            ft.Text(f"Quantity: {model.quantity.value}"),
            ft.Text(f"Total: ${model.total.value:.2f}"),
            ft.Button(
                content="Add item",
                on_click=lambda: model.quantity.update(lambda value: value + 1),
            ),
        ]
    )
```

Usa hooks, contextos y routers de Flet con normalidad. flet-mvc no introduce
un segundo sistema de renderizado.

Pasar el modelo completo hace que el componente observe los commits del
modelo. Para limitar el siguiente render a una parte más pequeña,
`use_datapoint(point)` se suscribe solo a ese datapoint y elimina la
suscripción cuando se desmonta el componente:

```python
from flet_mvc import use_datapoint


@ft.component
def QuantityValue(point) -> ft.Control:
    quantity = use_datapoint(point)
    return ft.Text(f"Quantity: {quantity}")
```

Como cualquier hook de Flet, llama `use_datapoint()` de forma incondicional y
solo dentro del cuerpo de un `@ft.component`.

Existen dos contratos de suscripción intencionalmente distintos:

| API | El callback recibe | Uso |
|---|---|---|
| `point.subscribe(...)` | un `DatapointChange` | Observar un valor concreto |
| `model.subscribe(...)` | `(sender, field)` | Contrato nativo de `ft.Observable` |

Un commit estable de datapoints notifica una vez al modelo con `field=None`.
`model.revision` aumenta una vez por cada commit, incluido un único incremento
para todo un `batch()` externo; las asignaciones sin cambio no lo aumentan.
Los atributos públicos normales del modelo conservan las notificaciones
habituales de Flet Observable con el nombre de su campo.

### Bindings imperativos con controles

Los bindings son útiles en una pantalla imperativa o cuando un control
concreto debe recibir cambios sin reconstruir un componente más grande.

```python
class ProfileModel(FletModel):
    @data
    def name(self) -> str:
        return "Ada"


model = ProfileModel()
field = ft.TextField(ref=model.name, label="Name")
preview = ft.Text(ref=model.name)

model.name.set("Grace")
assert field.value == "Grace"
assert preview.value == "Grace"
```

Para un control de entrada registrado, flet-mvc también envuelve su evento de
cambio actual. Al escribir en `field`, copia `field.value` al modelo, conserva
el manejador original del evento y propaga el resultado.

La inferencia automática está limitada deliberadamente a 21 controles que
tienen un único campo de estado estable. Nunca adivina propiedades
estructurales como `controls`, `content`, `actions`, `options` y `rows`.
Conéctalas de forma explícita:

```python
class BoardModel(FletModel):
    @data
    def cards(self) -> list[ft.Control]:
        return []


model = BoardModel()
board = ft.Column()
model.cards.bind(board, "controls")

model.cards.set([ft.Text("First"), ft.Text("Second")])
model.cards.sync()
model.cards.pull(board)
model.cards.unbind(board)
```

Los campos y eventos completos están en
[`docs/CONTROL_COMPATIBILITY.md`](https://github.com/o0Adrian/flet-mvc/blob/master/docs/CONTROL_COMPATIBILITY.md).

Para una clase de control personalizada con un campo de estado estable,
registra el contrato una vez:

```python
register_control_binding(
    MyControl,
    "selection",
    expected_type=str,
    event="on_change",
)
```

Para una sola instancia, prefiere
`point.bind(control, "selection")`. Un binding implícito desconocido o
inseguro produce `UnsupportedControlError` con instrucciones, en vez de
adivinar.

### Referencias a controles

Usa el `ft.Ref` propio de Flet cuando necesites el objeto del control y no un
valor reactivo:

```python
name_ref = ft.Ref[ft.TextField]()


async def focus_name() -> None:
    if name_ref.current is not None:
        await name_ref.current.focus()


field = ft.TextField(ref=name_ref, label="Name")
```

Mantén esta referencia junto a la UI que posee el control.

## Controles compuestos conectados al modelo

`FletComponent` es una subclase nativa de `ft.Column` con `@ft.control`. Úsala
cuando un control reutilizable necesite comunicarse con un modelo y gestionar
esa comunicación durante su ciclo de vida.

`@send(Model.field)` publica el valor devuelto por el método.
`@receive(Model.field)` se suscribe al montar y cancela la suscripción al
desmontar.

```python
import flet as ft

from flet_mvc import FletComponent, FletModel, data, receive, send


class CounterModel(FletModel):
    @data
    def count(self) -> int:
        return 0


@ft.control
class CounterPanel(FletComponent):
    def init(self) -> None:
        super().init()
        self.count_text = ft.Text(size=32)
        self.controls = [
            self.count_text,
            ft.Button(content="Add one", on_click=self.increment),
        ]

    @receive(CounterModel.count)
    def show_count(self, value: int) -> None:
        self.count_text.value = str(value)

    @send(CounterModel.count)
    def increment(self, _event=None) -> int:
        return self.model.count.value + 1


panel = CounterPanel(model=CounterModel())
```

Ambos decoradores aceptan métodos síncronos y asíncronos. `@receive` se
ejecuta inmediatamente de forma predeterminada; pasa
`fire_immediately=False` cuando solo importen los cambios posteriores.
Devuelve `NO_CHANGE` desde un método con `@send` cuando el evento no deba
modificar el destino. Devolver `None` sí establece el datapoint en `None`.

Un método `@send` asíncrono debe declararse con `async def`. Un `def` normal
que devuelva un awaitable produce `TypeError`, de acuerdo con el contrato de
eventos de Flet en vez de descartar silenciosamente la corrutina.

Después de que un receiver modifica controles hijos, `FletComponent` actualiza
únicamente su propio subárbol. Los componentes declarativos y controles
conectados en otro lugar conservan su propio ciclo de actualización de Flet;
un receiver no fuerza la actualización de toda la página.

Para la composición normal de UI, prefiere el `@ft.component` más ligero de
Flet. Usa `FletComponent` específicamente cuando send/receive y la limpieza
al desmontar sean útiles.

## Estructura MVC opcional

MVC es una división de directorios y responsabilidades, no una capa de runtime
obligatoria:

```text
my_app/
├── app.py
├── controllers/
│   └── todo.py
├── models/
│   └── todo.py
└── views/
    └── todo.py
```

- El **Modelo** contiene el estado y las reglas del dominio.
- La **Vista** devuelve controles nativos de Flet, un `ft.View` o un componente.
- El **Controlador** traduce acciones de la UI en operaciones del modelo.
- `app.py` crea objetos nuevos para la sesión y los conecta.

`models/todo.py`:

```python
from flet_mvc import FletModel, data


class TodoModel(FletModel):
    @data
    def title(self) -> str:
        return "Learn Flet MVC"
```

`controllers/todo.py`:

```python
from dataclasses import dataclass

from models.todo import TodoModel


@dataclass
class TodoController:
    model: TodoModel

    def rename(self, _event=None) -> None:
        self.model.title.set("Build the application")
```

`views/todo.py`:

```python
import flet as ft

from controllers.todo import TodoController


def build_view(controller: TodoController) -> ft.Control:
    return ft.Column(
        controls=[
            ft.Text(ref=controller.model.title, size=28),
            ft.Button(content="Rename", on_click=controller.rename),
        ]
    )
```

`app.py`:

```python
import flet as ft

from controllers.todo import TodoController
from models.todo import TodoModel
from views.todo import build_view


def main(page: ft.Page) -> None:
    model = TodoModel()
    controller = TodoController(model)
    page.add(build_view(controller))


if __name__ == "__main__":
    ft.run(main)
```

Crea el modelo dentro de `main()`. Flet invoca `main()` para cada sesión, por
lo que un modelo a nivel de módulo compartiría estado entre usuarios por
accidente.

El controlador es una clase normal de la aplicación; `@dataclass` solo elimina
código repetitivo. Una función o un objeto de servicio funciona igual de bien.
flet-mvc no exporta una clase base para controladores. Pasa `page` al
controlador sólo si realmente navega o abre un servicio de Flet. Usa Flet
directamente para diálogos, opciones de dropdown, actualizaciones y navegación.

## Routing y vistas nativas

Usa `ft.Router`, `ft.Route`, `ft.View` y `@ft.component` oficiales. flet-mvc
no mantiene un manejador de rutas paralelo.

```python
import flet as ft


@ft.component
def Home() -> ft.Control:
    return ft.Text("Home", size=28)


@ft.component
def About() -> ft.Control:
    return ft.Text("About", size=28)


@ft.component
def App() -> ft.Control:
    page = ft.context.page
    return ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Button(content="Home", on_click=lambda: page.navigate("/")),
                    ft.Button(
                        content="About",
                        on_click=lambda: page.navigate("/about"),
                    ),
                ]
            ),
            ft.Router(
                routes=[
                    ft.Route(index=True, component=Home),
                    ft.Route(path="about", component=About),
                ]
            ),
        ]
    )


def main(page: ft.Page) -> None:
    page.render(App)


if __name__ == "__main__":
    ft.run(main)
```

Para obtener gestos móviles de retroceso y una pila real de vistas, usa
`ft.Router(..., manage_views=True)`, devuelve objetos `ft.View` desde los
componentes de ruta y llama `page.render_views(App)`. Consulta la
[guía oficial de Router](https://flet.dev/docs/controls/router/) de Flet.

## Tablas de datos

`DataTableAdapter` construye y exporta un `ft.DataTable` nativo. El control de
Flet siempre está disponible mediante `adapter.control`.

### Carga registros

```python
import flet as ft

from flet_mvc import DataTableAdapter


adapter = DataTableAdapter().load_records(
    [
        {"name": "Ada", "score": 98},
        {"name": "Grace", "score": 95},
    ]
)

table_control = adapter.control
assert isinstance(table_control, ft.DataTable)
print(adapter.to_records())
print(adapter.to_csv())
```

Las claves se recopilan en el orden en que aparecen por primera vez. Los
valores ausentes se convierten en `None`.

### Define un esquema y sus filas

```python
adapter = DataTableAdapter()
adapter.set_columns(["name", "score"], numeric="score")
adapter.set_rows(
    [
        ["Ada", 98],
        {"name": "Grace", "score": 95},
    ]
)
```

Las filas pueden ser secuencias, mappings u objetos `ft.DataRow` existentes.
La cantidad de columnas y celdas visibles se valida antes de actualizar la
tabla.

### DataFrames y archivos CSV

```python
adapter.load_dataframe(frame)
frame_copy = adapter.to_dataframe()


async def export_table() -> None:
    await adapter.save_csv(file_name="scores.csv")
```

`load_dataframe()` acepta objetos de estilo pandas con
`to_dict(orient="records")` y de estilo Polars con `to_dicts()` sin importar
ninguna de las bibliotecas. `to_dataframe()` necesita pandas:

```bash
python -m pip install "flet-mvc[dataframe]>=1.0,<2"
```

`save_csv()` usa el `FilePicker.save_file()` asíncrono actual de Flet y envía
los bytes del CSV para guardarlos en escritorio o descargarlos en web.

La API canónica del adaptador es:

| Propósito | API |
|---|---|
| Tabla nativa | `control` |
| Definir contenido | `set_columns()`, `set_rows()` |
| Importar | `load_records()`, `load_dataframe()` |
| Exportar en memoria | `to_records()`, `to_csv()`, `to_dataframe()` |
| Guardar o descargar | `save_csv()` |

## Templates de proyecto

La CLI incluye cuatro puntos de partida ejecutables:

| Comando | Qué demuestra |
|---|---|
| `flet-mvc start -d my_app` | Proyecto MVC pequeño basado en clases |
| `flet-mvc reactive -d my_app` | Estado calculado y `FletComponent` |
| `flet-mvc routes -d my_app` | Router oficial de Flet y vistas nativas |
| `flet-mvc tabs -d my_app` | `Tabs`, `TabBar` y `TabBarView` actuales |

Previsualiza todos los archivos sin escribir:

```bash
flet-mvc reactive --destination my_app --dry-run
```

Los archivos existentes no se sobrescriben de forma predeterminada. Después
de revisar el destino, `--force` reemplaza los archivos del template:

```bash
flet-mvc reactive --destination my_app --force
```

Cada template incluye un README local breve y su propio `pyproject.toml`.

## Resumen de la API pública

| Área | Nombres públicos |
|---|---|
| Modelo | `FletModel`, `Datapoint`, `DatapointChange`, `data`, `computed` |
| Hook declarativo | `use_datapoint` |
| Binding | `register_control_binding` y excepciones de binding |
| Componentes | `FletComponent`, `send`, `receive`, `NO_CHANGE` |
| Tablas | `DataTableAdapter` |

Los errores principales son:

- `DatapointError`: error base del estado reactivo;
- `DatapointBindingError`: falló el binding o su sincronización atómica;
- `UnsupportedControlError`: no hay un campo seguro registrado;
- `DatapointDependencyError`: la declaración de dependencia no es válida;
- `DependencyCycleError`: el grafo contiene un ciclo.

Antes de publicar la API estable se eliminaron los alias de compatibilidad
pre-1.0 y las capas que duplicaban Flet. Los reemplazos exactos están en
[`MIGRATION.md`](https://github.com/o0Adrian/flet-mvc/blob/master/MIGRATION.md).

## Desarrollo

Instala el repositorio con las dependencias de desarrollo:

```bash
git clone https://github.com/o0Adrian/flet-mvc.git
cd flet-mvc
python -m pip install -e ".[dev]"
```

Ejecuta las comprobaciones rápidas:

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy
```

El repositorio también contiene pruebas reales de Flet en navegador, Pyodide,
templates generados e integración con paquetes. Consulta
[`CONTRIBUTING.md`](https://github.com/o0Adrian/flet-mvc/blob/master/CONTRIBUTING.md)
para ver el flujo completo.

## Licencia

MIT. Consulta [LICENSE](https://github.com/o0Adrian/flet-mvc/blob/master/LICENSE).
