# Melhorias Arquiteturais Avançadas - Princípios SOLID

## Status Atual ✅

O projeto já implementa:
- ✅ **Single Responsibility** - Classes com responsabilidades únicas
- ✅ **Open/Closed** - Extensível via interfaces (IChartProvider, IHttpClient)
- ✅ **Liskov Substitution** - Implementações substituíveis
- ✅ **Interface Segregation** - Interfaces pequenas e focadas
- ✅ **Dependency Inversion** - Dependency Injection em todo lugar
- ✅ **Strategy Pattern** - Para modos de update (Replace/Append)
- ✅ **Repository Pattern** - Para acesso a dados com cache
- ✅ **Factory Pattern** - Para criação de serviços
- ✅ **Value Objects** - Track, PlaylistMetadata
- ✅ **Result Pattern** - Para error handling funcional

## Melhorias Propostas 🚀

### 1. **Command Pattern** - CLI Commands Desacoplados

**Problema Atual**: CLI tem lógica procedural misturada com apresentação

**Solução**:
```python
# Interfaces
class ICommand(ABC):
    @abstractmethod
    def execute(self) -> Result[Any, Exception]:
        pass

class ICommandHandler(ABC):
    @abstractmethod
    def handle(self, command: ICommand) -> Result[Any, Exception]:
        pass

# Implementações
class CreatePlaylistCommand:
    def __init__(self, region: str, limit: int, name: str, public: bool, update_mode: str):
        self.region = region
        self.limit = limit
        self.name = name
        self.public = public
        self.update_mode = update_mode

class CreatePlaylistCommandHandler(ICommandHandler):
    def __init__(self, service: SpotifyService, scraper: IChartProvider):
        self._service = service
        self._scraper = scraper

    def handle(self, command: CreatePlaylistCommand) -> Result[PlaylistResult, Exception]:
        # Lógica de negócio pura, sem CLI
        pass
```

**Benefícios**:
- Separação total entre CLI e lógica de negócio
- Testabilidade melhorada
- Reutilização em outros contextos (API, GUI)
- Fácil adicionar undo/redo

---

### 2. **Observer Pattern** - Sistema de Eventos

**Problema Atual**: Progress tracking acoplado ao CLI

**Solução**:
```python
# Event System
class Event:
    pass

class TrackAddedEvent(Event):
    def __init__(self, track: Track, playlist_id: str):
        self.track = track
        self.playlist_id = playlist_id
        self.timestamp = datetime.now()

class IEventListener(ABC):
    @abstractmethod
    def on_event(self, event: Event) -> None:
        pass

class EventBus:
    def __init__(self):
        self._listeners: Dict[Type[Event], List[IEventListener]] = {}

    def subscribe(self, event_type: Type[Event], listener: IEventListener):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def publish(self, event: Event):
        event_type = type(event)
        for listener in self._listeners.get(event_type, []):
            listener.on_event(event)

# Listeners
class ProgressBarListener(IEventListener):
    def on_event(self, event: Event):
        if isinstance(event, TrackAddedEvent):
            # Update progress bar
            pass

class MetricsListener(IEventListener):
    def on_event(self, event: Event):
        # Log metrics
        pass
```

**Benefícios**:
- Desacoplamento total
- Fácil adicionar novos listeners
- Métricas e logging sem modificar código existente
- Event sourcing possível

---

### 3. **Specification Pattern** - Filtros Reutilizáveis

**Problema Atual**: Filtros hardcoded ou não existem

**Solução**:
```python
# Specification Pattern
class ISpecification(ABC, Generic[T]):
    @abstractmethod
    def is_satisfied_by(self, item: T) -> bool:
        pass

    def and_(self, other: 'ISpecification[T]') -> 'ISpecification[T]':
        return AndSpecification(self, other)

    def or_(self, other: 'ISpecification[T]') -> 'ISpecification[T]':
        return OrSpecification(self, other)

    def not_(self) -> 'ISpecification[T]':
        return NotSpecification(self)

# Specifications para Tracks
class PopularTrackSpecification(ISpecification[Track]):
    def __init__(self, min_popularity: int):
        self.min_popularity = min_popularity

    def is_satisfied_by(self, track: Track) -> bool:
        return track.popularity >= self.min_popularity

class DurationRangeSpecification(ISpecification[Track]):
    def __init__(self, min_ms: int, max_ms: int):
        self.min_ms = min_ms
        self.max_ms = max_ms

    def is_satisfied_by(self, track: Track) -> bool:
        return self.min_ms <= track.duration_ms <= self.max_ms

class ExplicitContentSpecification(ISpecification[Track]):
    def __init__(self, allow_explicit: bool):
        self.allow_explicit = allow_explicit

    def is_satisfied_by(self, track: Track) -> bool:
        return self.allow_explicit or not track.explicit

# Uso
spec = (PopularTrackSpecification(70)
        .and_(DurationRangeSpecification(120000, 300000))
        .and_(ExplicitContentSpecification(False)))

filtered_tracks = [t for t in tracks if spec.is_satisfied_by(t)]
```

**Benefícios**:
- Filtros reutilizáveis e combináveis
- Lógica de negócio expressiva
- Fácil testar
- Queries complexas de forma limpa

---

### 4. **Pipeline Pattern** - Processamento de Tracks

**Problema Atual**: Processamento linear e acoplado

**Solução**:
```python
# Pipeline Pattern
class IPipelineStep(ABC, Generic[T]):
    @abstractmethod
    def process(self, items: List[T]) -> List[T]:
        pass

class Pipeline(Generic[T]):
    def __init__(self):
        self._steps: List[IPipelineStep[T]] = []

    def add_step(self, step: IPipelineStep[T]) -> 'Pipeline[T]':
        self._steps.append(step)
        return self

    def execute(self, items: List[T]) -> List[T]:
        result = items
        for step in self._steps:
            result = step.process(result)
        return result

# Steps
class ValidateTrackStep(IPipelineStep[Track]):
    def process(self, tracks: List[Track]) -> List[Track]:
        return [t for t in tracks if t.id and len(t.id) > 0]

class RemoveDuplicatesStep(IPipelineStep[Track]):
    def process(self, tracks: List[Track]) -> List[Track]:
        seen = set()
        result = []
        for track in tracks:
            if track.id not in seen:
                seen.add(track.id)
                result.append(track)
        return result

class FilterBySpecificationStep(IPipelineStep[Track]):
    def __init__(self, spec: ISpecification[Track]):
        self.spec = spec

    def process(self, tracks: List[Track]) -> List[Track]:
        return [t for t in tracks if self.spec.is_satisfied_by(t)]

class EnrichTrackMetadataStep(IPipelineStep[Track]):
    def __init__(self, spotify_client: ITrackReader):
        self.client = spotify_client

    def process(self, tracks: List[Track]) -> List[Track]:
        enriched = []
        for track in tracks:
            metadata = self.client.track(track.id)
            if metadata:
                enriched.append(Track(
                    id=track.id,
                    name=metadata.get('name'),
                    artist=metadata.get('artists', [{}])[0].get('name'),
                    album=metadata.get('album', {}).get('name')
                ))
            else:
                enriched.append(track)
        return enriched

# Uso
pipeline = (Pipeline[Track]()
    .add_step(ValidateTrackStep())
    .add_step(RemoveDuplicatesStep())
    .add_step(FilterBySpecificationStep(
        PopularTrackSpecification(60)
        .and_(DurationRangeSpecification(120000, 400000))
    ))
    .add_step(EnrichTrackMetadataStep(spotify_client)))

processed_tracks = pipeline.execute(raw_tracks)
```

**Benefícios**:
- Processamento modular e reutilizável
- Fácil adicionar/remover steps
- Testável isoladamente
- Ordem configurável

---

### 5. **Builder Pattern** - Construção Complexa

**Problema Atual**: Criação de objetos complexos com muitos parâmetros

**Solução**:
```python
# Builder Pattern
class PlaylistBuilder:
    def __init__(self):
        self._metadata: Optional[PlaylistMetadata] = None
        self._tracks: List[Track] = []
        self._filters: List[ISpecification[Track]] = []
        self._pipeline: Optional[Pipeline[Track]] = None

    def with_metadata(self, metadata: PlaylistMetadata) -> 'PlaylistBuilder':
        self._metadata = metadata
        return self

    def with_name(self, name: str) -> 'PlaylistBuilder':
        if not self._metadata:
            self._metadata = PlaylistMetadata(name=name, description="")
        return self

    def add_tracks(self, tracks: List[Track]) -> 'PlaylistBuilder':
        self._tracks.extend(tracks)
        return self

    def add_filter(self, spec: ISpecification[Track]) -> 'PlaylistBuilder':
        self._filters.append(spec)
        return self

    def with_pipeline(self, pipeline: Pipeline[Track]) -> 'PlaylistBuilder':
        self._pipeline = pipeline
        return self

    def build(self) -> 'PlaylistRequest':
        # Apply filters
        filtered_tracks = self._tracks
        for spec in self._filters:
            filtered_tracks = [t for t in filtered_tracks if spec.is_satisfied_by(t)]

        # Apply pipeline
        if self._pipeline:
            filtered_tracks = self._pipeline.execute(filtered_tracks)

        return PlaylistRequest(
            metadata=self._metadata,
            tracks=filtered_tracks
        )

# Uso Fluent
playlist_request = (PlaylistBuilder()
    .with_name("Top Rock 2024")
    .add_tracks(scraped_tracks)
    .add_filter(GenreSpecification("rock"))
    .add_filter(PopularTrackSpecification(70))
    .with_pipeline(standard_pipeline)
    .build())
```

**Benefícios**:
- API fluente e intuitiva
- Validação em build()
- Imutabilidade
- Fácil criar variações

---

### 6. **DTO Pattern** - Transferência entre Camadas

**Problema Atual**: Dicts passando entre camadas

**Solução**:
```python
# DTOs
@dataclass(frozen=True)
class CreatePlaylistRequest:
    name: str
    description: str
    track_ids: List[str]
    public: bool = False
    update_mode: str = "replace"

@dataclass(frozen=True)
class CreatePlaylistResponse:
    playlist_url: str
    tracks_added: int
    tracks_failed: int
    was_updated: bool
    errors: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class ScrapedChartDTO:
    region: str
    tracks: List[Track]
    scraped_at: datetime
    total_tracks: int

# Service Layer usa DTOs
class PlaylistApplicationService:
    def create_playlist(self, request: CreatePlaylistRequest) -> Result[CreatePlaylistResponse, Exception]:
        # Validação
        if not request.name:
            return Failure(ValidationError("Name is required"))

        # Lógica
        # ...

        return Success(CreatePlaylistResponse(
            playlist_url=url,
            tracks_added=count,
            tracks_failed=failed,
            was_updated=updated
        ))
```

**Benefícios**:
- Contratos claros entre camadas
- Type safety
- Validação centralizada
- Documentação viva

---

### 7. **Decorator Pattern** - Adicionar Funcionalidades

**Problema Atual**: Difícil adicionar logging, metrics, caching

**Solução**:
```python
# Decorators para Services
class LoggingServiceDecorator(IPlaylistOperations):
    def __init__(self, wrapped: IPlaylistOperations, logger: logging.Logger):
        self._wrapped = wrapped
        self._logger = logger

    def create(self, name: str, description: str, public: bool = False):
        self._logger.info(f"Creating playlist: {name}")
        start = time.time()
        try:
            result = self._wrapped.create(name, description, public)
            duration = time.time() - start
            self._logger.info(f"Playlist created in {duration:.2f}s")
            return result
        except Exception as e:
            self._logger.error(f"Failed to create playlist: {e}")
            raise

class MetricsServiceDecorator(IPlaylistOperations):
    def __init__(self, wrapped: IPlaylistOperations):
        self._wrapped = wrapped
        self._metrics = {"creates": 0, "errors": 0}

    def create(self, name: str, description: str, public: bool = False):
        try:
            result = self._wrapped.create(name, description, public)
            self._metrics["creates"] += 1
            return result
        except Exception:
            self._metrics["errors"] += 1
            raise

class RetryServiceDecorator(IPlaylistOperations):
    def __init__(self, wrapped: IPlaylistOperations, max_retries: int = 3):
        self._wrapped = wrapped
        self._max_retries = max_retries

    def create(self, name: str, description: str, public: bool = False):
        for attempt in range(self._max_retries):
            try:
                return self._wrapped.create(name, description, public)
            except Exception as e:
                if attempt == self._max_retries - 1:
                    raise
                time.sleep(2 ** attempt)

# Composição
service = RetryServiceDecorator(
    MetricsServiceDecorator(
        LoggingServiceDecorator(
            PlaylistManager(client, cache),
            logger
        )
    ),
    max_retries=3
)
```

**Benefícios**:
- Adicionar funcionalidades sem modificar código
- Composição flexível
- Cross-cutting concerns separados
- Fácil testar

---

### 8. **Validation Layer** - Validação Estruturada

**Solução**:
```python
# Validation
class IValidator(ABC, Generic[T]):
    @abstractmethod
    def validate(self, item: T) -> Result[T, List[ValidationError]]:
        pass

class PlaylistRequestValidator(IValidator[CreatePlaylistRequest]):
    def validate(self, request: CreatePlaylistRequest) -> Result[CreatePlaylistRequest, List[ValidationError]]:
        errors = []

        if not request.name or len(request.name.strip()) == 0:
            errors.append(ValidationError("Playlist name is required"))

        if len(request.name) > 100:
            errors.append(ValidationError("Playlist name too long (max 100)"))

        if request.update_mode not in ["replace", "append", "new"]:
            errors.append(ValidationError(f"Invalid update mode: {request.update_mode}"))

        if len(request.track_ids) == 0:
            errors.append(ValidationError("At least one track is required"))

        if len(request.track_ids) > 10000:
            errors.append(ValidationError("Too many tracks (max 10000)"))

        return Failure(errors) if errors else Success(request)
```

---

## Arquitetura Recomendada 🏗️

```
┌─────────────────────────────────────────────────────────┐
│                   CLI Layer (Click)                      │
│  - Command Handlers                                      │
│  - Event Listeners (Progress, Logging)                  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Application Layer                           │
│  - Commands & Handlers                                   │
│  - DTOs (Request/Response)                              │
│  - Validators                                           │
│  - Event Bus                                            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                Domain Layer                              │
│  - Value Objects (Track, PlaylistMetadata)             │
│  - Specifications (Filters)                             │
│  - Pipelines (Processing)                               │
│  - Builders                                             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│             Infrastructure Layer                         │
│  - Repositories (with caching)                          │
│  - External APIs (Spotify, Kworb)                       │
│  - Strategies (Replace, Append)                         │
│  - Factories                                            │
└─────────────────────────────────────────────────────────┘
```

## Prioridades de Implementação 📋

### Alta Prioridade (Impacto Alto):
1. ✅ **Command Pattern** - Separa CLI de lógica
2. ✅ **Observer Pattern** - Sistema de eventos
3. ✅ **Pipeline Pattern** - Processamento modular

### Média Prioridade (Qualidade):
4. ✅ **Specification Pattern** - Filtros reutilizáveis
5. ✅ **DTO Pattern** - Contratos claros
6. ✅ **Validation Layer** - Validação estruturada

### Baixa Prioridade (Nice to have):
7. ⚠️ **Decorator Pattern** - Cross-cutting concerns
8. ⚠️ **Builder Pattern** - API fluente

## Conclusão

Essas melhorias tornarão o projeto ainda mais:
- **Testável** - Cada componente isolado
- **Manutenível** - Código limpo e organizado
- **Extensível** - Fácil adicionar features
- **Profissional** - Padrões de mercado
- **Escalável** - Arquitetura sólida

Quer que eu implemente alguma dessas melhorias?
