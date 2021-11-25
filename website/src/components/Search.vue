<template>
  <div class="search">
      <ul>
        <li v-for="image in images" :key="image">
          <img :src="imageUrl(image)" width="512" height="512" />
        </li>
      </ul>
  </div>
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component';
import axios from "axios";
import {Watch, Prop} from "vue-property-decorator";


export default class SearchResults extends Vue {
  @Prop({required: true})
  searchTerm!: string
  images = [];

  mounted() {
    if (this.searchTerm.length > 0) {
      this.search();
    }
  }

  @Watch("searchTerm")
  doSearch(){
    this.search();
  }

  search(): void {
    console.log(process.env.VUE_APP_BASE_API_URL)
    axios.get(process.env.VUE_APP_BASE_API_URL + '/search/' + this.searchTerm)
        .then(response => {
          this.images = response.data;
        })
        .catch(error => {
          console.log(error);
        });
  }

    imageUrl(image: string): string {
      return process.env.VUE_APP_BASE_API_URL + '/content/' + image;
    }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>
