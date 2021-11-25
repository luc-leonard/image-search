<template>
  <div id="embeds"></div>
  <div id="tooltip"></div>
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component';
import axios from "axios";
import * as d3 from "d3";
import {Prop, Watch} from "vue-property-decorator";


class Embed{
  constructor(readonly path: string, readonly x: number, readonly y: number, readonly color: string) {}
}


export default class HelloWorld extends Vue {
  embeds: Embed[] = [];
  @Prop({required: true})
  term = "";


  @Watch("term")
  onTermChange(value: string, oldValue: string) {
    this.getEmbeds();
  }

  getEmbeds() {
      axios.get(process.env.VUE_APP_BASE_API_URL + '/embeddings/' + this.term)
      .then(response => {
        this.embeds = response.data
        this.showEmbeds();
      })
      .catch(error => {
        console.log(error);
      });
  }

  mounted(): void {
    this.getEmbeds();
  }

  mouseover(d: any, i: any): void {
    const selected = arguments[2][arguments[1]]
    const src = process.env.VUE_APP_BASE_API_URL + '/content/' + d.path;
    const html = `<img src=${src} width="128px">`;
    d3.select(selected).style("fill", "blue");
    d3.select("#tooltip").style("opacity", 1)
        .html(html)
        .style("left", (event as any).pageX + "px")
        .style("top", (event as any).pageY + "px");
  }

  mouseout(d: any, i: any): void {
    const selected = arguments[2][arguments[1]]
    d3.select("#tooltip").style("opacity", 0)
    if (!d.path.startsWith('text')) {
      d3.select(selected).style("fill", d.color);
    }
  }

  showEmbeds(): void {
    d3.select("#embeds").selectAll("*").remove();
    var embeds = d3.select("#embeds")
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%');
    embeds.selectAll('dot')
        .data(this.embeds.slice(0, 15000))
        .enter()
        .append("circle")
          .attr('cx', function(d: Embed) { return (d.x + 100) * 5; })
          .attr('cy', function(d: Embed) { return (d.y + 100) * 5; })
          .attr('r', 5)
          .style('fill', function(d: Embed) { return d.color;})
          .on("mouseover", this.mouseover)
          .on("mouseout", this.mouseout);

  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
#embeds {
  width: 100%;
  height: 100%;
}
#tooltip {
    position: absolute;
    text-align: center;
    width: 60px;
    height: 28px;
    padding: 2px;
    font: 12px sans-serif;
    background: lightsteelblue;
    border: 0px;
    border-radius: 8px;
    pointer-events: none;
}
</style>
