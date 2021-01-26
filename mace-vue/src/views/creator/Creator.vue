<template>
  <v-container>
    <v-row>
      <Toolbox 
      v-on:grid_changed="update_grid"
      v-on:radius_changed="update_radius"
      v-on:save="save"
      v-on:load="load"
      v-on:clear="clear"
      />
    </v-row>
    <v-row
      align="center"
      justify="space-around">
      <v-col cols='8' ref='scenarioCanvas'>
        <v-stage ref="stage"
          :config="configKonva"
          @dragstart="handleDragstart"
          @dragend="handleDragend"
          @click="handleClick">
          <v-layer>
            <v-rect :config="configMapBack"
            />
          </v-layer>
          <v-layer ref="gridLayer">
            <v-line
              v-for="item in vLines"
              :key="item.id"
              :config="item">
            </v-line>
            <v-line
              v-for="item in hLines"
              :key="item.id"
              :config="item">
            </v-line>
          </v-layer>
          <v-layer ref="layer">
            <v-circle
              :config="{
                x: item.x,
                y: item.y,
                radius: 50,
                fill: '#111111',
                radius: radius,
                draggable: false,
                opacity: 0.05,
                stroke: '#1100FF',
                strokeWidth: 1
              }"
              v-for="item in list"
              :key="item.id">
            </v-circle>
            <v-circle
              v-for="item in list"
              :key="item.id"
              :config="item">
            </v-circle>
            <v-text
              :config="{
                  text: item._id,
                  fontSize: 9,
                  x: item.x-4,
                  y: item.y+8
                }"
              v-for="item in list"
              v-bind:key="item._id">
            </v-text>
          </v-layer>
        </v-stage>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import Toolbox from '@/views/creator/Toolbox'


export default {
  name: 'Creator',
  components: {
    Toolbox
  },
  data () {
    return {
      filename: 'export.json',
      importFile: '',
      configKonva: {
        width: 1110,
        height: 600
      },
      selectedType: {
        id: 1,
        title: 'Manual'
      },
      gridSize: 50,
      configMapBack: {
        x: 0,
        y: 0,
        width: 0,
        height: 0,
        fill: '#FFFFFF',
        shadowBlur: 0
      },
      list: [],
      radius: 120,
      hLines: [],
      vLines: [],
      nodes: 0,
    }
  },
  mounted () {
    this.createGrid()
  },
  methods: {
    handleDragstart () {
    },
    save () {
      const blob = new Blob([JSON.stringify(this.list)], {type: 'text/json'})
      const e = document.createEvent('MouseEvents')
      const a = document.createElement('a')
      a.download = this.filename
      a.href = window.URL.createObjectURL(blob)
      a.dataset.downloadurl = ['text/json', a.download, a.href].join(':')
      e.initEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null)
      a.dispatchEvent(e)
    },
    load (file) {
      var reader = new FileReader()
      reader.onload = (file) => {
        this.list = JSON.parse(file.target.result)
      }
      reader.readAsText(file)
    },
    clear () {
      this.list = []
      this.nodes = 0
      this.importFile = ''
    },
    handleDragend (event) {
      if (((event.target.attrs.x > 0) && (event.target.attrs.x < this.configKonva.width)) && ((event.target.attrs.y > 0) && (event.target.attrs.y < this.configKonva.height))) {
        this.list[event.target.attrs._id].x = event.target.attrs.x
        this.list[event.target.attrs._id].y = event.target.attrs.y
      } else {
        this.list.splice(event.target.attrs._id, 1)
        for (let i = event.target.attrs._id; i < this.list.length; i++) {
          this.list[i]._id = i
        }
        this.nodes--
      }
    },
    handleClick (evt) {
      if (this.selectedType.title === 'Manual') {
        const stage = evt.target.getStage()
        const pos = stage.getPointerPosition()
        this.list.push({
          _id: this.nodes,
          x: pos.x,
          y: pos.y,
          fill: '#1100FF',
          stroke: 'black',
          strokeWidth: 0,
          shadowBlur: 1,
          shadowOffset: {x: 2, y: 2},
          shadowOpacity: 0.2,
          opacity: 0.8,
          draggable: true,
          radius: 6,
          shadowColor: 'black',
          type: 'node'
        })
        this.nodes++
      }
    },
    update_grid (event) {
      this.gridSize = event
    },
    update_radius (event) {
      this.radius = event
    },
    createGrid () {
      if (this.configKonva.width > this.$refs.scenarioCanvas.clientWidth) {
        this.$nextTick(() => {
          this.configKonva.width = this.$refs.scenarioCanvas.clientWidth
          this.configMapBack.width = this.configKonva.width
        })
      } else if (this.configKonva.width < 1) {
        this.$nextTick(() => {
          this.configKonva.width = 1
          this.configMapBack.width = this.configKonva.width
        })
      }
      if (this.configKonva.height > this.$refs.scenarioCanvas.clientHeight) {
        this.$nextTick(() => {
          this.configKonva.height = this.$refs.scenarioCanvas.clientHeight
          this.configMapBack.height = this.configKonva.height
        })
      } else if (this.configKonva.height < 1) {
        this.$nextTick(() => {
          this.configKonva.height = 1
          this.configMapBack.height = this.configKonva.height
        })
      }
      this.hLines = []
      for (let i = 0; i < this.configKonva.height / this.gridSize; i++) {
        this.hLines.push({
          _id: i,
          points: [0, Math.round(i * this.gridSize), Number(this.configKonva.width), Math.round(i * this.gridSize)],
          stroke: '#111111',
          strokeWidth: 0.3
        })
      }
      this.vLines = []
      for (let j = 0; j < this.configKonva.width / this.gridSize; j++) {
        this.vLines.push({
          _id: j,
          points: [Math.round(j * this.gridSize), 0, Math.round(j * this.gridSize), Number(this.configKonva.height)],
          stroke: '#111111',
          strokeWidth: 0.2
        })
      }
      this.configMapBack.width = this.configKonva.width
      this.configMapBack.height = this.configKonva.height
    }
  },
  watch: {
    configKonva: {
      handler () {
        this.createGrid()
      },
      deep: true
    },
    gridSize: function () {
      this.createGrid()
    },
    grid: function (newVal) {
      this.handleGrid(newVal)
    },
    list: function () {
      this.nodes = this.list.length
    }
  }
}
</script>

<style>

</style>