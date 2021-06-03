<template>
  <v-container>
    <v-row>
      <Toolbox 
        v-on:gridsize_changed="update_gridsize"
        v-on:range_changed="update_range"
        v-on:save="save"
        v-on:load="load"
        v-on:clear="clear"
        :grid=grid
        :policy=policy
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
                radius: item.range,
                fill: '#111111',
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
                  text: item.id,
                  fontSize: 9,
                  x: item.x-4,
                  y: item.y+8
                }"
              v-for="item in list"
              v-bind:key="item.id">
            </v-text>
          </v-layer>
        </v-stage>
      </v-col>
    </v-row>
    <v-dialog
      v-model="node_settings_dialog"
      persistent
      max-width="600px"
    >
      <v-card>
        <v-card-title>
          <span class="headline">Node Settings</span>
        </v-card-title>
        <v-card-text>
          <v-container>
            <v-row>
              <v-col>
                <v-text-field
                  label="Capacity"
                  dense
                  hint="Maximum load capacity"
                  v-model="new_node.capacity"
                ></v-text-field>
              </v-col>
              <v-col>
                <v-text-field
                  label="Performance"
                  dense
                  hint="Node Performance"
                  v-model="new_node.performance"
                ></v-text-field>
              </v-col>
              <v-col>
                <v-text-field
                  label="Consumption"
                  dense
                  hint="Node consumption"
                  v-model="new_node.consumption"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-row>
              <v-col>
                <v-text-field
                  label="Price"
                  dense
                  hint="Node price"
                  v-model="new_node.price"
                ></v-text-field>
              </v-col>
              <v-col>
                <v-text-field
                  label="Rate"
                  dense
                  hint="Node rate"
                  v-model="new_node.rate"
                ></v-text-field>
              </v-col>
              <v-col>
                <v-text-field
                  label="Waiting time"
                  dense
                  hint="Node Waiting time"
                  v-model="new_node.waiting_time"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-row>
              <v-col>
                <v-combobox
                  v-model="new_node.duration"
                  :items="['Porte10','Porte20']"
                  label="Duration"
                  
                  dense
                  hint="Task creation Duration"
                ></v-combobox>
              </v-col>
            </v-row>
            <v-row>
            <v-col cols="2">
              <v-text-field
                v-model="new_node.range"
                solo
                dense
                label="Range"
              ></v-text-field>
            </v-col>
            <v-col cols="10">
              <v-slider
                class="pt-1"
                dense
                v-model="new_node.range"
                label="Range"
                :max="255"
              ></v-slider>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="2">
              <v-text-field
                dense
                v-model="new_node.z"
                solo
                label="Z"
              ></v-text-field>
            </v-col>
            <v-col cols="10">
              <v-slider
                :min="0"
                class="pt-1"
                dense
                v-model="new_node.z"
                label="Z"
                :max="1000"
              ></v-slider>
            </v-col>
          </v-row>
          </v-container>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="blue darken-1"
            text
            @click="node_settings_dialog = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="blue darken-1"
            text
            @click="add_node"
          >
            Add
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import Toolbox from '@/views/dnetflow/Toolbox'


export default {
  name: 'Creator',
  components: {
    Toolbox
  },
  data () {
    return {
      node_settings_dialog: false,
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
      range: 120,
      hLines: [],
      vLines: [],
      nodes: 0,
      grid: {
        QMax: 50,
        ThetaMax: 20.0,
        NumericalDiscretizationWorkload: 100,
        NumericalDiscretizationWaiting: 100,
        TpsDec: 1.0,
        EpsRelGain: 0.1
      },
      policy: {
        Energy: 0.0,
        Price: 0.0,
        Performance: 1.0,
      },
      current_pos: {
        x: 0,
        y: 0
      },
      new_node: {
        id: 0,
        capacity: 1000,
        performance: 1.0,
        consumption: 1.0,
        price: 1.0,
        rate: 100.0,
        waiting_time: 2.0,
        duration: "Porte20",
        x: 0,
        y: 0,
        z: 0,
        range: 90
      }
    }
  },
  mounted () {
    this.createGrid()
  },
  methods: {
    open_node_settings () {
      this.node_settings_dialog = true
    },
    close_node_settings () {
      this.node_settings_dialog = false
    },
    handleDragstart () {
    },
    save () {
      const blob = new Blob([JSON.stringify({"Cluster": this.$options.filters.filter_to_save(this.list), "Grid": this.grid, "Policy": this.policy}, null, 2)], {type: 'text/json'})
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
        this.list[event.target.attrs.id].x = event.target.attrs.x
        this.list[event.target.attrs.id].y = event.target.attrs.y
      } else {
        this.list.splice(event.target.attrs.id, 1)
        for (let i = event.target.attrs.id; i < this.list.length; i++) {
          this.list[i].id = i
        }
        this.nodes--
      }
    },
    handleClick (evt) {
      if (this.selectedType.title === 'Manual') {
        this.open_node_settings()
        const stage = evt.target.getStage()
        this.current_pos = stage.getPointerPosition()
      }
    },
    add_node () {
      this.list.push({
        id: this.nodes,
        x: this.current_pos.x,
        y: this.current_pos.y,
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
        type: 'node',
        range: this.new_node.range,
        capacity: this.new_node.capacity,
        performance: this.new_node.performance,
        consumption: this.new_node.consumption,
        price: this.new_node.price,
        rate: this.new_node.rate,
        waiting_time: this.new_node.waiting_time,
        duration: this.new_node.duration,
        z: this.new_node.z,
      })
      this.nodes++
      this.close_node_settings()
    },
    update_gridsize (event) {
      this.gridSize = event
    },
    update_range (event) {
      this.range = event
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
          id: j,
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
  },
  filters: {
    filter_to_save: function (items) {
      var new_list = []
      items.forEach(item => {
        new_list.push({
          id: item.id+1,
          Capacity: parseInt(item.capacity,10),
          Performance: parseFloat(item.performance,10),
          Consumption: parseFloat(item.consumption,10),
          Price: parseFloat(item.price,10),
          Rate: parseFloat(item.rate,10),
          WaitingTime: parseFloat(item.waiting_time,10),
          Duration: item.duration,
          X: parseInt(item.x,10),
          Y: parseInt(item.y,10),
          Z: parseInt(item.z,10),
          Range: parseInt(item.range,10)
        })
      });
      return new_list
    }
  }
}
</script>

<style>

</style>