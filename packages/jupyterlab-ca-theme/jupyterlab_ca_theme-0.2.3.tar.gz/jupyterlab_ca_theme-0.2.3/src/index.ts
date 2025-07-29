import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { IThemeManager } from '@jupyterlab/apputils';

import {
  IDisposable, DisposableDelegate
} from '@lumino/disposable';

import {
  Dialog,
  ISplashScreen
} from '@jupyterlab/apputils';

import '../style/index.css';

import { CommandRegistry } from '@lumino/commands';

namespace CommandIDs {
  export const changeTheme = 'apputils:change-theme';

  export const loadState = 'apputils:load-statedb';

  export const recoverState = 'apputils:recover-statedb';

  export const reset = 'apputils:reset';

  export const resetOnLoad = 'apputils:reset-on-load';

  export const saveState = 'apputils:save-statedb';
}

/**
 * Initialization data for the jupyterlab_ca_theme extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab_ca_theme:plugin',
  description: 'A JupyterLab extension theme for Composable Analytics DataLabs.',
  autoStart: true,
  requires: [IThemeManager],
  activate: (app: JupyterFrontEnd, manager: IThemeManager) => {
    console.log('JupyterLab extension jupyterlab_ca_theme is activated!');
    const style = 'jupyterlab_ca_theme/index.css';

    manager.register({
      name: 'jupyterlab_ca_theme',
      isLight: true,
      load: () => manager.loadCSS(style),
      unload: () => Promise.resolve(undefined)
    });
  }
};

const splash: JupyterFrontEndPlugin<ISplashScreen> = {
  id: '@jupyterlab/mysplash:splash',
  autoStart: true,
  provides: ISplashScreen,
  activate: (app: any) => {
      return {
          show: (light = true) => {
              const { commands, restored } = app;

              return Private.showSplash(restored, commands, CommandIDs.reset, light);
          }
      };
  }
};

namespace Private {
  /**
   * Create a splash element.
   */
  function createSplash() {
      const splash = document.createElement('div');
      splash.classList.add('loading-overlay');
      const loadingSVG = document.createElement('div');
      loadingSVG.classList.add('loading-svg');
      const svg = document.createElementNS('http://www.w3.org/2000/svg', "svg")
      svg.id = 'layer1';
      svg.setAttribute('x', '0px');
      svg.setAttribute('y', '0px');
      svg.setAttribute('viewBox', '0 0 219.9 265.9');
      svg.setAttribute('xml:space', 'preserve');
      const styleTag = document.createElement('style');
      styleTag.setAttribute('type', 'text/css');
      styleTag.innerHTML = `.pol2.st0{fill:none;stroke:#d2d6de;stroke-miterlimit:10; stroke-width: 3}
                            .pol1.st0{fill:none;stroke:#0c4e7d;stroke-miterlimit:10; stroke-width: 4}`;
      svg.appendChild(styleTag);
      const g1 = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      const polygon1 = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
      polygon1.setAttribute('class', 'pol2 st0');
      polygon1.setAttribute('points', '0.5,177.5 0.5,71.5 119,0.9 119,106.9 77.3,131.7');
      g1.appendChild(polygon1);
      const polyline1 = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
      polyline1.setAttribute('class', 'pol2 st0');
      polyline1.setAttribute('points', '77.3,131.7 77.3,226 0.5,177.5');
      g1.appendChild(polyline1);
      svg.appendChild(g1);
      const g2 = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      const polygon2 = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
      polygon2.setAttribute('class', 'pol2 st0');
      polygon2.setAttribute('points', '219.3,88.4 219.3,194.4 100.8,265 100.8,159 142.4,134.1');
      g2.appendChild(polygon2);
      const polyline2 = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
      polyline2.setAttribute('class', 'pol2 st0');
      polyline2.setAttribute('points', '142.4,134.1 142.4,39.9 219.3,88.4');
      g2.appendChild(polyline2);
      svg.appendChild(g2);

      const g3 = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      const polygon3 = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
      polygon3.setAttribute('class', 'pol1 st0');
      polygon3.setAttribute('points', '0.5,177.5 0.5,71.5 119,0.9 119,106.9 77.3,131.7');
      g3.appendChild(polygon3);
      const polyline3 = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
      polyline3.setAttribute('class', 'pol1 st0');
      polyline3.setAttribute('points', '77.3,131.7 77.3,226 0.5,177.5');
      g3.appendChild(polyline3);
      svg.appendChild(g3);
      const g4 = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      const polygon4 = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
      polygon4.setAttribute('class', 'pol1 st0');
      polygon4.setAttribute('points', '219.3,88.4 219.3,194.4 100.8,265 100.8,159 142.4,134.1');
      g4.appendChild(polygon4);
      const polyline4 = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
      polyline4.setAttribute('class', 'pol1 st0');
      polyline4.setAttribute('points', '142.4,134.1 142.4,39.9 219.3,88.4');
      g4.appendChild(polyline4);
      svg.appendChild(g4);
      loadingSVG.appendChild(svg);
      let leftLine1 = document.createElement("div");
      let leftLine2 = document.createElement("div");
      let leftLine3 = document.createElement("div");
      let leftLine4 = document.createElement("div");
      let leftLine5Wrap = document.createElement("div");
      let leftLine5 = document.createElement("div");
      let leftLine6 = document.createElement("div");

      leftLine1.setAttribute('class', 'line left-line-1');
      leftLine2.setAttribute('class', 'line left-line-2');
      leftLine3.setAttribute('class', 'line left-line-3');
      leftLine4.setAttribute('class', 'line left-line-4');
      leftLine5Wrap.setAttribute('class', 'line left-line-5-wrap');
      leftLine5.setAttribute('class', 'line left-line-5');
      leftLine6.setAttribute('class', 'line left-line-6');

      leftLine5Wrap.appendChild(leftLine5);
      loadingSVG.appendChild(leftLine1);
      loadingSVG.appendChild(leftLine2);
      loadingSVG.appendChild(leftLine3);
      loadingSVG.appendChild(leftLine4);
      loadingSVG.appendChild(leftLine5Wrap);
      loadingSVG.appendChild(leftLine6);

      let rightLine1 = document.createElement("div");
      let rightLine2 = document.createElement("div");
      let rightLine3 = document.createElement("div");
      let rightLine4 = document.createElement("div");
      let rightLine5Wrap = document.createElement("div");
      let rightLine5 = document.createElement("div");
      let rightLine6 = document.createElement("div");

      rightLine1.setAttribute('class', 'line right-line-1');
      rightLine2.setAttribute('class', 'line right-line-2');
      rightLine3.setAttribute('class', 'line right-line-3');
      rightLine4.setAttribute('class', 'line right-line-4');
      rightLine5Wrap.setAttribute('class', 'line right-line-5-wrap');
      rightLine5.setAttribute('class', 'line right-line-5');
      rightLine6.setAttribute('class', 'line right-line-6');

      rightLine5Wrap.appendChild(rightLine5);
      loadingSVG.appendChild(rightLine1);
      loadingSVG.appendChild(rightLine2);
      loadingSVG.appendChild(rightLine3);
      loadingSVG.appendChild(rightLine4);
      loadingSVG.appendChild(rightLine5Wrap);
      loadingSVG.appendChild(rightLine6);
      splash.appendChild(loadingSVG);
      return splash;
  }

  /**
   * A debouncer for recovery attempts.
   */
  let debouncer = 0;

  /**
   * The recovery dialog.
   */
  let dialog: Dialog<any>;

  /**
   * Allows the user to clear state if splash screen takes too long.
   */
  function recover(fn: () => void): void {
      if (dialog) {
          return;
      }

      dialog = new Dialog({
          title: 'Loading...',
          body: `The loading screen is taking a long time.
      Would you like to clear the workspace or keep waiting?`,
          buttons: [
              Dialog.cancelButton({ label: 'Keep Waiting' }),
              Dialog.warnButton({ label: 'Clear Workspace' })
          ]
      });

      dialog
          .launch()
          .then(result => {
              if (result.button.accept) {
                  return fn();
              }

              dialog.dispose();
              //dialog = null;

              debouncer = window.setTimeout(() => {
                  recover(fn);
              }, 700);
          })
          .catch(() => {
              /* no-op */
          });
  }

  /**
   * The splash element.
   */
  const splash = createSplash();

  /**
   * The splash screen counter.
   */
  let splashCount = 0;

  /**
   * Show the splash element.
   *
   * @param ready - A promise that must be resolved before splash disappears.
   *
   * @param recovery - A command that recovers from a hanging splash.
   */
  export function showSplash(
      ready: Promise<any>,
      commands: CommandRegistry,
      recovery: string,
      light: boolean
  ): IDisposable {
      splash.classList.remove('splash-fade');
      splash.classList.toggle('light', light);
      splash.classList.toggle('dark', !light);
      splashCount++;

      if (debouncer) {
          window.clearTimeout(debouncer);
      }
      debouncer = window.setTimeout(() => {
          if (commands.hasCommand(recovery)) {
              recover(() => {
                  commands.execute(recovery, {});
              });
          }
      }, 7000);

      document.body.appendChild(splash);

      return new DisposableDelegate(() => {
          ready.then(() => {
              if (--splashCount === 0) {
                  if (debouncer) {
                      window.clearTimeout(debouncer);
                      debouncer = 0;
                  }

                  if (dialog) {
                      dialog.dispose();
                      //dialog = null;
                  }

                  splash.classList.add('splash-fade');
                  window.setTimeout(() => {
                      document.body.removeChild(splash);
                  }, 500);
              }
          });
      });
  }
}

const plugins: JupyterFrontEndPlugin<any>[] = [
  plugin,
  splash
];

export default plugins;