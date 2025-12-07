<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as THREE from 'three';
import * as OBC from '@thatopen/components';
import { API_BASE_URL } from '../config';

const props = defineProps<{
  filePath?: string;
}>();

const emit = defineEmits<{
  (e: 'loaded'): void;
  (e: 'error', message: string): void;
}>();

const containerRef = ref<HTMLDivElement | null>(null);
const isLoading = ref(false);
const loadingProgress = ref(0);
const loadingStatus = ref('');
const hasModel = ref(false);
const error = ref<string | null>(null);

let components: OBC.Components | null = null;
let world: OBC.SimpleWorld<OBC.SimpleScene, OBC.SimpleCamera, OBC.SimpleRenderer> | null = null;
let fragments: OBC.FragmentsManager | null = null;
let ifcLoader: OBC.IfcLoader | null = null;

async function initViewer() {
  if (!containerRef.value) return;

  try {
    // Create components instance
    components = new OBC.Components();

    // Get worlds manager and create a world
    const worlds = components.get(OBC.Worlds);
    world = worlds.create<OBC.SimpleScene, OBC.SimpleCamera, OBC.SimpleRenderer>();

    // Setup scene, renderer, camera
    world.scene = new OBC.SimpleScene(components);
    world.renderer = new OBC.SimpleRenderer(components, containerRef.value);
    world.camera = new OBC.SimpleCamera(components);

    // Initialize components
    components.init();

    // Setup scene (adds lights)
    world.scene.setup();

    // Set background color
    world.scene.three.background = new THREE.Color(0x1a1a2e);

    // Add grid
    const grids = components.get(OBC.Grids);
    grids.create(world);

    // Get fragments manager
    fragments = components.get(OBC.FragmentsManager);

    // Handle model loaded via groups
    fragments.onFragmentsLoaded.add((group) => {
      if (world) {
        world.scene.three.add(group);
      }
    });

    // Setup IFC loader with CDN WASM path
    ifcLoader = components.get(OBC.IfcLoader);

    // Configure web-ifc WASM location
    ifcLoader.settings.wasm = {
      path: "https://unpkg.com/web-ifc@0.0.68/",
      absolute: true,
    };

    await ifcLoader.setup();

    // Set initial camera position
    await world.camera.controls.setLookAt(50, 30, 50, 0, 0, 0);

    console.log('IFC Viewer initialized');
  } catch (err) {
    console.error('Error initializing viewer:', err);
    error.value = err instanceof Error ? err.message : 'Failed to initialize viewer';
    emit('error', error.value);
  }
}

async function loadIfcFile(filePath: string) {
  if (!ifcLoader || !world || !fragments) {
    error.value = 'Viewer not initialized';
    return;
  }

  isLoading.value = true;
  loadingProgress.value = 0;
  loadingStatus.value = 'Fetching file...';
  error.value = null;

  try {
    // Fetch the file
    const fileUrl = filePath.startsWith('http')
      ? filePath
      : `${API_BASE_URL}/${filePath}`;

    console.log('Loading IFC from:', fileUrl);

    const response = await fetch(fileUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch file: ${response.statusText}`);
    }

    loadingStatus.value = 'Converting IFC to fragments...';
    loadingProgress.value = 30;

    const data = await response.arrayBuffer();
    const buffer = new Uint8Array(data);

    // Load the IFC file - returns FragmentsGroup
    const modelId = filePath.split('/').pop()?.split('.')[0] || 'model';

    console.log('Starting IFC load, buffer size:', buffer.length, 'bytes');

    // IfcLoader.load takes (data, coordinate?, name?)
    const group = await ifcLoader.load(buffer, true, modelId);

    console.log('IFC loaded successfully, group:', group);

    loadingProgress.value = 100;
    loadingStatus.value = 'Complete!';
    hasModel.value = true;

    // Fit camera to model using the returned group
    if (group && world) {
      // Get bounding box and fit camera
      const bbox = new THREE.Box3();
      group.traverse((child: THREE.Object3D) => {
        if (child instanceof THREE.Mesh) {
          bbox.expandByObject(child);
        }
      });

      if (!bbox.isEmpty()) {
        const center = new THREE.Vector3();
        bbox.getCenter(center);
        const size = new THREE.Vector3();
        bbox.getSize(size);
        const maxDim = Math.max(size.x, size.y, size.z);

        await world.camera.controls.setLookAt(
          center.x + maxDim,
          center.y + maxDim * 0.5,
          center.z + maxDim,
          center.x,
          center.y,
          center.z
        );
      }
    }

    emit('loaded');
  } catch (err) {
    console.error('Error loading IFC:', err);
    error.value = err instanceof Error ? err.message : 'Failed to load IFC file';
    emit('error', error.value);
  } finally {
    isLoading.value = false;
    setTimeout(() => {
      loadingStatus.value = '';
    }, 2000);
  }
}

function clearModel() {
  if (fragments && world) {
    // Remove all groups from scene and dispose
    for (const group of fragments.groups.values()) {
      world.scene.three.remove(group);
      fragments.disposeGroup(group);
    }
    hasModel.value = false;
  }
}

function resetCamera() {
  if (world) {
    world.camera.controls.setLookAt(50, 30, 50, 0, 0, 0);
  }
}

// Watch for file path changes
watch(() => props.filePath, async (newPath) => {
  if (newPath) {
    await loadIfcFile(newPath);
  }
});

onMounted(async () => {
  await initViewer();

  // If file path provided, load it
  if (props.filePath) {
    await loadIfcFile(props.filePath);
  }
});

onUnmounted(() => {
  if (components) {
    components.dispose();
    components = null;
    world = null;
    fragments = null;
    ifcLoader = null;
  }
});

// Expose methods for parent component
defineExpose({
  loadIfcFile,
  clearModel,
  resetCamera,
  hasModel
});
</script>

<template>
  <div class="relative w-full h-full bg-buildos-dark rounded-lg overflow-hidden">
    <!-- 3D Container -->
    <div ref="containerRef" class="w-full h-full" />

    <!-- Loading overlay -->
    <div
      v-if="isLoading"
      class="absolute inset-0 bg-black/70 flex flex-col items-center justify-center"
    >
      <div class="w-64 space-y-4">
        <div class="text-center text-white">
          <div class="text-lg font-medium mb-2">Loading IFC Model</div>
          <div class="text-sm text-gray-400">{{ loadingStatus }}</div>
        </div>

        <!-- Progress bar -->
        <div class="h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            class="h-full bg-buildos-primary transition-all duration-300"
            :style="{ width: `${loadingProgress}%` }"
          />
        </div>

        <div class="text-center text-sm text-gray-400">
          {{ Math.round(loadingProgress) }}%
        </div>
      </div>
    </div>

    <!-- Error message -->
    <div
      v-if="error && !isLoading"
      class="absolute inset-0 bg-black/70 flex items-center justify-center"
    >
      <div class="text-center p-6">
        <div class="text-red-400 text-lg mb-2">Failed to load model</div>
        <div class="text-gray-400 text-sm">{{ error }}</div>
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-if="!hasModel && !isLoading && !error"
      class="absolute inset-0 flex items-center justify-center pointer-events-none"
    >
      <div class="text-center text-gray-500">
        <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <p>Upload an IFC file to view</p>
      </div>
    </div>

    <!-- Controls -->
    <div
      v-if="hasModel"
      class="absolute top-4 right-4 flex gap-2"
    >
      <button
        @click="resetCamera"
        class="p-2 bg-gray-800/80 hover:bg-gray-700 rounded-lg text-white transition-colors"
        title="Reset camera"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M15 10l-4 4m0 0l-4-4m4 4V3m0 18a9 9 0 110-18 9 9 0 010 18z" />
        </svg>
      </button>
      <button
        @click="clearModel"
        class="p-2 bg-gray-800/80 hover:bg-red-600 rounded-lg text-white transition-colors"
        title="Clear model"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>

    <!-- Instructions -->
    <div
      v-if="hasModel"
      class="absolute bottom-4 left-4 text-xs text-gray-500 bg-black/50 px-3 py-2 rounded"
    >
      <span class="mr-3">🖱️ Rotate: Left click + drag</span>
      <span class="mr-3">🔍 Zoom: Scroll</span>
      <span>✋ Pan: Right click + drag</span>
    </div>
  </div>
</template>
