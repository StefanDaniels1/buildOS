Worlds
Creating our 3D world

In this tutorial you'll learn how to create a simple scene using @thatopen/components.

Hello world! A world represents a 3D environment in your application. It consists of a scene, a camera and (optionally) a renderer. You can create multiple worlds and show them in multiple viewports at the same time.

In this tutorial, we will import:

Three.js to get some 3D entities for our app.

@thatopen/components to set up the barebone of our app.

@thatopen/ui to add some simple and cool UI menus.

Stats.js (optional) to measure the performance of our app.

import * as THREE from "three";
import Stats from "stats.js";
import * as BUI from "@thatopen/ui";
// You have to import * as OBC from "@thatopen/components"
import * as OBC from "../..";

Getting the container

Next, we need to tell the library where do we want to render the 3D scene. We have added a DIV element to this HTML page that occupies the whole width and height of the viewport. Let's fetch it by its ID:

const container = document.getElementById("container")!;

Creating a components instance

Now we will create a new instance of the Components class. This class is the main entry point of the library. It will be used to register and manage all the components in your application.

Don't forget to dispose it when you are done!

const components = new OBC.Components();

Setting up the world

Now we are ready to create our first world. We will use the Worlds component to manage all the worlds in your application. Instead of instancing it, we can get it from the Components instance. All components are singleton, so this is always a better way to get them.

const worlds = components.get(OBC.Worlds);


We can create a new world by calling the create method of the Worlds component. It's a generic method, so we can specify the type of the scene, the camera and the renderer we want to use.

const world = worlds.create<
  OBC.SimpleScene,
  OBC.SimpleCamera,
  OBC.SimpleRenderer
>();


Now we can set the scene, the camera and the renderer of the world, and call the init method to start the rendering process.

world.scene = new OBC.SimpleScene(components);
world.renderer = new OBC.SimpleRenderer(components, container);
world.camera = new OBC.SimpleCamera(components);

components.init();


We could add some lights, but the SimpleScene class can do that easier for us using its setup method:

world.scene.setup();


We'll make the background of the scene transparent so that it looks good in our docs page, but you don't have to do that in your app!

world.scene.three.background = null;

Adding things to our scene

Now we are ready to start adding some 3D entities to our scene. We will load a Fragments model:

const workerUrl =
  "https://thatopen.github.io/engine_fragment/resources/worker.mjs";
const fragments = components.get(OBC.FragmentsManager);
fragments.init(workerUrl);

world.camera.controls.addEventListener("rest", () =>
  fragments.core.update(true),
);
fragments.list.onItemSet.add(({ value: model }) => {
  model.useCamera(world.camera.three);
  world.scene.three.add(model.object);
  fragments.core.update(true);
});

const fragPaths = ["https://thatopen.github.io/engine_components/resources/frags/school_arq.frag"];
await Promise.all(
  fragPaths.map(async (path) => {
    const modelId = path.split("/").pop()?.split(".").shift();
    if (!modelId) return null;
    const file = await fetch(path);
    const buffer = await file.arrayBuffer();
    return fragments.core.load(buffer, { modelId });
  }),
);


Finally, we will make the camera look at the model:

await world.camera.controls.setLookAt(68, 23, -8.5, 21.5, -5.5, 23);
await fragments.core.update(true);

Adding some UI

We will use @thatopen/ui library to add some simple and cool UI elements to our app. First, we need to call the init method of the BUI.Manager class to initialize the library:

BUI.Manager.init();


Now we will create a new panel with some inputs to change the background color of the scene and the intensity of the directional and ambient lights. For more information about the UI library, you can check the specific documentation for it!

const panel = BUI.Component.create<BUI.PanelSection>(() => {
  return BUI.html`
    <bim-panel label="Worlds Tutorial" class="options-menu">
      <bim-panel-section label="Controls">

        <bim-color-input
          label="Background Color" color="#202932"
          @input="${({ target }: { target: BUI.ColorInput }) => {
            world.scene.config.backgroundColor = new THREE.Color(target.color);
          }}">
        </bim-color-input>
        <bim-number-input
          slider step="0.1" label="Directional lights intensity" value="1.5" min="0.1" max="10"
          @change="${({ target }: { target: BUI.NumberInput }) => {
            world.scene.config.directionalLight.intensity = target.value;
          }}">
        </bim-number-input>
        <bim-number-input
          slider step="0.1" label="Ambient light intensity" value="1" min="0.1" max="5"
          @change="${({ target }: { target: BUI.NumberInput }) => {
            world.scene.config.ambientLight.intensity = target.value;
          }}">
        </bim-number-input>

      </bim-panel-section>
    </bim-panel>
    `;
});
document.body.append(panel);


And we will make some logic that adds a button to the screen when the user is visiting our app from their phone, allowing to show or hide the menu. Otherwise, the menu would make the app unusable.

const button = BUI.Component.create<BUI.PanelSection>(() => {
  return BUI.html`
      <bim-button class="phone-menu-toggler" icon="solar:settings-bold"
        @click="${() => {
          if (panel.classList.contains("options-menu-visible")) {
            panel.classList.remove("options-menu-visible");
          } else {
            panel.classList.add("options-menu-visible");
          }
        }}">
      </bim-button>
    `;
});
document.body.append(button);

Measuring the performance (optional)

We'll use Stats.js to measure the performance of our app. We will add it to the top left corner of the viewport. This way, we'll make sure that the memory consumption and the FPS of our app are under control.

const stats = new Stats();
stats.showPanel(2);
document.body.append(stats.dom);
stats.dom.style.left = "0px";
stats.dom.style.zIndex = "unset";

world.renderer.onBeforeUpdate.add(() => stats.begin());
world.renderer.onAfterUpdate.add(() => stats.end());

Wrap up

That's it! You have created your first 3D world and added some UI elements to it. You can now play with the inputs to see how the scene changes.

If you like, I can convert the entire docs set (for “Core → Worlds”, plus related parts) into a ready-to-use Markdown file for your agent (with correct links and structure).

IfcLoader
Purpose

The IfcLoader component converts IFC-files into Fragments (the library’s internal format), then loads them into the 3D scene. This is the recommended way to import BIM models, because the engine doesn’t load raw IFC directly. 
docs.thatopen.com
+1

Prerequisites / Setup

Assume you already have a basic world set up (scene, camera, renderer), e.g.:

world.scene = new OBC.SimpleScene(components);
world.scene.setup();
world.scene.three.background = null;

const container = document.getElementById("container")!;
world.renderer = new OBC.SimpleRenderer(components, container);
world.camera = new OBC.OrthoPerspectiveCamera(components);
await world.camera.controls.setLookAt(78, 20, -2.2, 26, -4, 25);

components.init();

components.get(OBC.Grids).create(world);


docs.thatopen.com

✨ Using The IfcLoader Component

Get the IfcLoader instance from your components:

const ifcLoader = components.get(OBC.IfcLoader);


Configure the loader / Web-IFC setup (setting WASM path etc.):

await ifcLoader.setup({
  autoSetWasm: false,
  wasm: {
    path: "https://unpkg.com/web-ifc@0.0.72/",
    absolute: true,
  },
});


docs.thatopen.com

Initialize the fragment manager (since IFC will be converted to Fragments, and those are handled by a separate component):

const workerUrl =
  "https://thatopen.github.io/engine_fragment/resources/worker.mjs";
const fragments = components.get(OBC.FragmentsManager);
fragments.init(workerUrl);

world.camera.controls.addEventListener("rest", () =>
  fragments.core.update(true),
);

fragments.list.onItemSet.add(({ value: model }) => {
  model.useCamera(world.camera.three);
  world.scene.three.add(model.object);
  fragments.core.update(true);
});


docs.thatopen.com

Define and call a function to load an IFC file (by fetching it, reading buffer, and passing to loader):

const loadIfc = async (path: string) => {
  const file = await fetch(path);
  const data = await file.arrayBuffer();
  const buffer = new Uint8Array(data);
  await ifcLoader.load(buffer, false, "example", {
    processData: {
      progressCallback: (progress) => console.log(progress),
    },
  });
};


You can then call loadIfc("https://thatopen.github.io/engine_components/resources/ifc/school_str.ifc"), or any valid IFC URL. 
docs.thatopen.com

After Loading — Exporting as Fragments

Once the IFC is converted and loaded as a Fragment model, you may want to export it (so you can re-use the fragment instead of re-converting IFC every time):

const downloadFragments = async () => {
  const [model] = fragments.list.values();
  if (!model) return;
  const fragsBuffer = await model.getBuffer(false);
  const file = new File([fragsBuffer], "school_str.frag");
  const link = document.createElement("a");
  link.href = URL.createObjectURL(file);
  link.download = file.name;
  link.click();
  URL.revokeObjectURL(link.href);
};


After that, you can load the .frag file directly instead of loading the original IFC + converting it, which is more efficient. 
docs.thatopen.com

(Optional) UI Integration

Optionally, you can integrate UI controls (using @thatopen/ui) to allow users to load IFCs, show progress, and download the Fragments. E.g.:

BUI.Manager.init();

const [panel, updatePanel] = BUI.Component.create<BUI.PanelSection, {}>((_) => {
  let downloadBtn: BUI.TemplateResult | undefined;
  if (fragments.list.size > 0) {
    downloadBtn = BUI.html`
      <bim-button label="Download Fragments" @click=${downloadFragments}></bim-button>
    `;
  }

  let loadBtn: BUI.TemplateResult | undefined;
  if (fragments.list.size === 0) {
    const onLoadIfc = async ({ target }: { target: BUI.Button }) => {
      target.label = "Conversion in progress...";
      target.loading = true;
      await loadIfc("https://thatopen.github.io/engine_components/resources/ifc/school_str.ifc");
      target.loading = false;
      target.label = "Load IFC";
    };

    loadBtn = BUI.html`
      <bim-button label="Load IFC" @click=${onLoadIfc}></bim-button>
      <bim-label>Open the console to see the progress!</bim-label>
    `;
  }

  return BUI.html`
    <bim-panel active label="IfcLoader Tutorial" class="options-menu">
      <bim-panel-section label="Controls">
        ${loadBtn}
        ${downloadBtn}
      </bim-panel-section>
    </bim-panel>
  `;
}, {});


(This will show a UI panel with buttons to load IFC and download resulting Fragments.) 
docs.thatopen.com

Summary & Notes

The engine does not load IFC directly — IFC must first be converted to Fragments. IfcLoader handles this conversion + loading. 
docs.thatopen.com
+1

Once converted, using Fragment format is much faster for loading BIM models than reloading IFC every time. The documentation suggests this is the preferred workflow. 
docs.thatopen.com
+1

The IfcLoader component exposes settings and lifecycle events (setup, onIfcImporterInitialized, etc.) for advanced configuration. 
docs.thatopen.com

If you like: I can produce a ready-to-use full Markdown file for the IfcLoader tutorial — with proper front-matter (title, metadata) and maybe link anchors — so it's easy for your agent to ingest as a doc.