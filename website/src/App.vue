<template>
      Search:
      <input type="text" v-model="termTmp" @keypress.enter="doSearch"/>
      <ScatterEmbeds :term="term"></ScatterEmbeds>
      <SearchResults :search-term="term" />

</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component';
import HelloWorld from './components/HelloWorld.vue';
import SearchResults from "@/components/Search.vue";
import ScatterEmbeds from "@/components/ScatterEmbeds.vue";

@Options({
  components: {
    ScatterEmbeds,
    SearchResults,
    HelloWorld,
  },
})
export default class App extends Vue {
  termTmp = new URL(location.href).searchParams.get('q') || '';
  term = this.termTmp

  doSearch() {
    this.term = this.termTmp;
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
