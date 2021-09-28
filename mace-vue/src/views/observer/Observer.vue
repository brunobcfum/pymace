<template>
    <v-container ref='canv'>
      <v-row>
        <v-col cols="3" class="ml-3 mr-3">
          <v-row
          justify="space-around">
            <v-card
              class="mx-auto"
              outlined
              elevation="3"
            >
              <v-list-item three-line>
                <v-list-item-content>
                  <div class="overline mb-4">
                    <v-chip
                      v-if="isConnected"
                      class="ma-2"
                      label
                      color="primary"
                    >
                      Live view
                    </v-chip>
                    <v-chip
                    v-if="!isConnected"
                      class="ma-2"
                      label
                      color="red"
                    >
                      Offline
                    </v-chip>

                  </div>
                  <v-list-item-subtitle>Model: {{ wlan.model }}</v-list-item-subtitle>
                  <v-list-item-subtitle>Range: {{ wlan.range }}  m</v-list-item-subtitle>
                  <v-list-item-subtitle>Bandwidth: {{ bandwidth }} MBps</v-list-item-subtitle>
                  <v-list-item-subtitle>Delay: {{ wlan.delay }} us</v-list-item-subtitle>
                  <v-list-item-subtitle>Error rate: {{ wlan.error }} %</v-list-item-subtitle>
                  <v-list-item-subtitle>Jitter: {{ wlan.jitter }} us</v-list-item-subtitle>
                </v-list-item-content>
                  <v-icon
                    large
                  >
                    mdi-antenna
                  </v-icon>
              </v-list-item>
            </v-card>
          </v-row>
          <v-row
          class="mt-3"
          justify="space-around">
            <v-card
              class="mx-auto"
              outlined
              elevation="3"
            >
              <v-list-item three-line>
                <v-list-item-content>
                  <div class="overline mb-4">
                    Settings
                  </div>
                <v-list-item-subtitle>
                  <v-switch
                  class="pl-3"
                  v-model="options.graph"
                  label="Connection Line"
                  ></v-switch>
                </v-list-item-subtitle>
                <v-list-item-subtitle>
                  <v-switch
                    class="pl-3"
                    v-model="options.radio"
                    label="Radio Range"
                  ></v-switch>
                </v-list-item-subtitle>
                <v-list-item-subtitle>
                  <v-row>
                    <v-switch
                      class="pl-3"
                      v-model="options.nodeid"
                      label="Node ID"
                    ></v-switch>
                    <v-text-field
                      class="ml-5 mr-5"
                      label="Font size"
                      type="number"
                      v-model="options.nodeid_size"
                      placeholder="Placeholder"
                    ></v-text-field>
                  </v-row>

                </v-list-item-subtitle>
                <v-list-item-subtitle>

                </v-list-item-subtitle>
                </v-list-item-content>
                  <v-icon
                    large
                  >
                    mdi-cog
                  </v-icon>
              </v-list-item>
            </v-card>
          </v-row>
        </v-col>
        <v-col cols="8">
          <v-row
            align="center"
            justify="space-around"
            ref='scenarioCanvas'>
              <v-stage ref="stage"
                @dragstart="handleDragStart"
                @dragend="handleDragEnd"
                :config="configKonva">
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
                <v-layer ref="graph" v-if="options.graph">
                  <v-line
                    v-for="item in graphlines"
                    :key="item.id"
                    :config="item">
                  </v-line>
                </v-layer>
                <v-layer ref="radio" v-if="options.radio">
                  <v-circle
                    :config="{
                      x: item.x,
                      y: item.y,
                      radius: item.range,
                      fill: '#000088',
                      draggable: false,
                      opacity: 0.05,
                      stroke: '#1100FF',
                      strokeWidth: 1
                    }"
                    v-for="item in list"
                    :key="item.id">
                  </v-circle>
                </v-layer>
                <v-layer ref="nodeid" v-if="options.nodeid">
                  <v-text
                    :config="{
                        text: item._id,
                        fontSize: options.nodeid_size,
                        x: item.x-4,
                        y: item.y+12
                      }"
                    v-for="item in list"
                    v-bind:key="item._id">
                  </v-text>
                </v-layer>
                <v-layer ref="nodes">
                  <v-circle
                    :config="{
                      x: item.x - 7,
                      y: item.y - 7,
                      radius: item.radius/2,
                      fill: '#1100FF',
                      stroke: 'black',
                      strokeWidth: 0,
                      opacity: 0.8,
                      strokeWidth: 1
                    }"
                    v-for="item in list"
                    :key="item.id">
                  </v-circle>
                  <v-circle
                    :config="{
                      x: item.x + 7,
                      y: item.y + 7,
                      radius: item.radius/2,
                      fill: '#1100FF',
                      stroke: 'black',
                      strokeWidth: 0,
                      opacity: 0.8,
                      strokeWidth: 1
                    }"
                    v-for="item in list"
                    :key="item.id">
                  </v-circle>
                  <v-circle
                    :config="{
                      x: item.x + 7,
                      y: item.y - 7,
                      radius: item.radius/2,
                      fill: '#1100FF',
                      stroke: 'black',
                      strokeWidth: 0,
                      opacity: 0.8,
                      strokeWidth: 1
                    }"
                    v-for="item in list"
                    :key="item.id">
                  </v-circle>
                  <v-circle
                    :config="{
                      x: item.x - 7,
                      y: item.y + 7,
                      radius: item.radius/2,
                      fill: '#1100FF',
                      stroke: 'black',
                      strokeWidth: 0,
                      opacity: 0.8,
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
                </v-layer>
              </v-stage>
          </v-row>
          <v-btn
            @click="reset"
            block
            color="yellow"
            small>
            Reset
          </v-btn>
        </v-col>
      </v-row>
  </v-container>
</template>

<script>
export default {
  name: 'Observer',
  components: {
  },
  data () {
    return {
      leader: '',
      configKonva: {
        width: 1110,
        height: 600
      },
      configCanvas: {
        width: 750,
        height: 700,
        verticalAlign: 'middle'
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
      range: 120,
      hLines: [],
      vLines: [],
      graphlines: [],
      nodes: 0,
      wlan: {},
      isConnected: false,
      options: {
        graph: true,
        radio: true,
        nodeid: true,
        nodeid_size: 9
      },
      x_start: 0,
      y_start: 0
    }
  },
  mounted () {
    this.createGrid()
    this.configCanvas.width = this.$refs.canv.clientWidth
    this.configMapBack.width = this.$refs.canv.clientWidth
  },
  methods : {
    handleDragStart (event) {
      this.x_start = event.target.attrs.x
      this.y_start = event.target.attrs.y
    },
    handleDragEnd (event) {
      console.log(event.target.attrs._id)
      var node = {
        id: event.target.attrs._id,
        x: event.target.attrs.x,
        y: event.target.attrs.y
      }
      if (((event.target.attrs.x > 0) && (event.target.attrs.x < this.configKonva.width)) && ((event.target.attrs.y > 0) && (event.target.attrs.y < this.configKonva.height))) {
        this.list[event.target.attrs._id].x = event.target.attrs.x
        this.list[event.target.attrs._id].y = event.target.attrs.y
      } else {
        this.list[event.target.attrs._id].x = this.x_start
        this.list[event.target.attrs._id].y = this.y_start
      }
      this.emit_new_position(node)
      // this.list = []
    },
    emit_new_position (node) {
      this.$socket.client.emit('update_pos', {node: node});
    },
    reset () {
      this.$socket.client.emit('reset_pos');
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
    },
    update_canvas () {
      this.configCanvas.width = this.$refs.scenarioCanvas.clientWidth
      this.configMapBack.width = this.$refs.scenarioCanvas.clientWidth
      this.createGrid()
    },
    update_graph () {
      this.graphlines = []
      var counter = 0
      this.list.forEach(node1 => {
        this.list.forEach(node2 => {
          if (this.euclidean_distance(node1, node2) <= this.wlan.range) {
            this.graphlines.push({
              _id: counter,
              points: [node1.x, node1.y, node2.x, node2.y],
              stroke: '#FF0022',
              strokeWidth: 0.5
            })
          }
          counter++
        })
      })
    },
    euclidean_distance (node1, node2) {
      return Math.round(Math.sqrt(Math.pow(node1.x - node2.x,2) + Math.pow(node1.y - node2.y,2)))
    }
  },
  sockets: {
    nodes (_data) {
      if (!this.isConnected) {
        this.isConnected = true
      }
      var data = _data.data
      this.wlan = data.wlan
      this.list = []
      for (let n = 0; n < data.nodes.length; n++) {
        var fill = '#1100FF'
        var x = data.nodes[n].position[0]
        var y = data.nodes[n].position[1]
        var z = data.nodes[n].position[2]
        if (n === parseInt(localStorage.getItem('leader'), 10)) {
          fill = '#FF0000'
        }
        this.list.push({
          _id: n,
          coreid: data.nodes[n].id,
          x: x,
          y: y,
          z: z,
          fill: fill,
          stroke: 'black',
          strokeWidth: 0,
          shadowBlur: 1,
          shadowOffset: {x: 2, y: 2},
          shadowOpacity: 0.2,
          opacity: 0.8,
          draggable: true,
          radius: 6,
          shadowColor: 'black',
          type: 'mote',
          range: data.nodes[n].range
        })
      }
      this.update_graph()
    },
    connect () {
      this.isConnected = true
    },
    disconnect () {
      this.isConnected = false
    },
    digest (data) {
      localStorage.setItem('leader', data.data.leader)
      this.leader = data.data.leader
    }
  },
  watch: {
    configCanvas: {
      handler () {
        this.createGrid()
      }
    }
  },
  beforeDestroy () {
    clearInterval(this.timer)
  },
  created () {
    // window.addEventListener("resize", this.update_canvas)
  },
  computed: {
    bandwidth () {
      return Math.ceil(this.wlan.bandwidth / (1024 * 1024))
    }
  }
}
</script>

<style>

</style>