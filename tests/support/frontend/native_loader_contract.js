'use strict';
// Contract model of the inspected CT SDK/kB, NOT execution of the native loader.
class NativeLoaderContract {
    constructor(importer, sdk) { this.importer = importer; this.sdk = sdk || new Map(); this.pending = {}; this.previous = null; }
    identity(url) { return Symbol.for(url.split('mono/')[1] || 'unknown'); }
    async load(url) {
        if (!url) { throw new Error('incorrect url'); }
        const id = this.identity(url);
        if (this.sdk.has(id)) { return this.sdk.get(id); }
        const entry = await this.importer(url);
        if (!entry.default || typeof entry.default.plugin !== 'function') { throw new Error('Not is plugin'); }
        const plugin = await entry.default.plugin({id, url});
        this.sdk.set(id, plugin);
        return {id, init: plugin.init, destroy: async () => { this.sdk.delete(id); await plugin.destroy(); }};
    }
    reconcile(urls) {
        const previous = this.previous;
        this.previous = (async () => {
            await previous;
            await Promise.all(Object.keys(this.pending).filter(url => !urls.includes(url)).map(async url => {
                const {plugin} = await this.pending[url]; await plugin.destroy(); delete this.pending[url];
            }));
            return Promise.allSettled(urls.map(url => {
                if (!this.pending[url]) {
                    this.pending[url] = this.load(url).then(plugin => plugin.init().then(result => ({plugin, result})));
                }
                return this.pending[url];
            }));
        })();
        return this.previous;
    }
}
module.exports = {NativeLoaderContract};
