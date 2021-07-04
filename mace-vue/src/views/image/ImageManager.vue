<template>
  <div>
    <v-data-table
      :headers="fields"
      :items="images"
      item-key="name"
      multi-sort
      class="elevation-2 ma-5"
    >
      <template v-slot:item.action="{ item }">
        <v-tooltip bottom>
          <template v-slot:activator="{ on, attrs }">
            <v-icon
              color="primary"
              @click="copyItem(item)"
              v-bind="attrs"
              v-on="on"
            >
              mdi-content-duplicate
            </v-icon>
          </template>
          <span>Duplicate</span>
        </v-tooltip>
        <v-tooltip bottom>
          <template v-slot:activator="{ on, attrs }">
            <v-icon
              color="primary"
              @click="editItem(item)"
              v-bind="attrs"
              v-on="on"
            >
              mdi-square-edit-outline
            </v-icon>
          </template>
          <span>Edit</span>
        </v-tooltip>
        <v-tooltip bottom>
          <template v-slot:activator="{ on, attrs }">
            <v-icon
              color="error"
              @click="deleteConfirm(item)"
              v-bind="attrs"
              v-on="on"
            >
              mdi-delete-empty
            </v-icon>
          </template>
          <span>Delete</span>
        </v-tooltip>

      </template>

      <template v-slot:top>
        <v-toolbar dark flat color="blue-grey darken-2">
          <v-toolbar-title>Available Images</v-toolbar-title>
          <v-divider
            class="mx-4"
            inset
            vertical
          ></v-divider>
          <v-btn class="ml-1" color="blue" @click="importDialog = !importDialog">
            Import
          </v-btn>
          <v-btn class="ml-1" color="blue" @click="_export">
            Export
          </v-btn>
          <template v-slot:extension>
            <v-btn
              fab
              color="blue-grey lighten-1"
              bottom
              right
              absolute
              @click="addItem"
            >
              <v-icon>mdi-plus</v-icon>
            </v-btn>
          </template>
          <v-spacer></v-spacer>
          <v-dialog v-model="dialog" max-width="600px" max-heigth="300px">
            <v-card class="mx-auto">
              <v-card-title>
                <span class="headline">{{ formTitle }}</span>
              </v-card-title>

              <v-card-text>
                  <v-row class="mt-4">
                  <v-text-field dense v-model="editedItem.id" label="Image ID"></v-text-field>
                  <v-icon
                    small
                    @click="genid()"
                  >
                    mdi-recycle
                  </v-icon>
                  </v-row>
                  <v-row>
                  <v-text-field dense v-model="editedItem.name" label="Image Name"></v-text-field>
                  </v-row>
                <v-col>
                  <v-combobox
                    v-model="editedItem.type"
                    :items="types"
                    label="Image type"
                    outlined
                    dense
                  ></v-combobox>
                </v-col>

                <v-textarea
                  v-model="editedItem.description"
                  filled
                  auto-grow
                  label="Image Description"
                  rows="4"
                  row-height="30"
                  shaped
                ></v-textarea>
                   <v-text-field
                    dense
                    v-model="editedItem.imagefile"
                    label="Paste image file path"
                  ></v-text-field>
                  <v-text-field
                    dense
                    v-model="editedItem.kernel"
                    label="Paste kernel file path"
                  ></v-text-field>
                  <v-text-field
                    dense
                    v-model="editedItem.initrd"
                    label="Paste initrd file path"
                  ></v-text-field>
                  <v-text-field
                    dense
                    v-model="editedItem.dtb"
                    label="Paste dtb file path"
                  ></v-text-field>
              </v-card-text>

              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="blue darken-4" @click="close">Cancel</v-btn>
                <v-btn color="blue darken-1" @click="save">Save</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
          <v-dialog v-model="deleteDialog" max-width="600px" max-heigth="300px">
            <v-card class="mx-auto">
              <v-card-title>
                <span class="headline">Really delete?</span>
              </v-card-title>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="blue darken-4" @click="close">Cancel</v-btn>
                <v-btn color="red darken-1" @click="deleteItem">Delete</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
          <v-dialog v-model="importDialog" max-width="600px" max-heigth="300px">
            <v-card class="mx-auto">
              <v-card-title>
                <span class="headline">Select file to import</span>
              </v-card-title>
              <v-card-text>
    
                <v-alert
                  dense
                  border="left"
                  type="warning"
                >
                  Any existing local configuration will be <strong>lost</strong> when importing from existing file
                </v-alert>
                <v-file-input
                  dense
                  solo
                  v-model="importFile"
                  accept="application/json"
                  label="Import from file"
                ></v-file-input>
              </v-card-text>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="blue darken-4" @click="close">Cancel</v-btn>
                <v-btn color="red darken-1" @click="_import">Import</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </v-toolbar>
      </template>
    </v-data-table>
  </div>
</template>



<script>
import crypto from 'crypto'

export default {
  name: 'ImageManager',
  data () {
    return {
      filename: 'export.json',
      images: [],
      importFile: {},
      types: [
        "Raspberry PI",
        "Linux"
      ],
      deleteDialog: false,
      importDialog: false,
      dialog: false,
      fields: [
        {
          value: 'id',
          text: 'ID',
          sortable: false
        },
        {
          value: 'name',
          text: 'Name',
          sortable: false
        },
        {
          value: 'type',
          text: 'Type',
          sortable: true
        },
        {
          value: 'kernel',
          text: 'Kernel',
          sortable: true
        },
        {
          value: 'action',
          text: 'Action',
          sortable: true,
          thStyle: {width: '200px'}
        },
        { text: '', value: 'data-table-expand' }
      ],
      editedIndex: -1,
      editedItem: {
        id: '',
        kernel: '',
        initrd: '',
        imagefile: '',
        dtb: '',
        name: '',
        description: '',
        type: ''
      },
      defaultItem: {
        id: '',
        kernel: '',
        initrd: '',
        imagefile: '',
        dtb: '',
        name: '',
        description: '',
        type: ''
      }
    }
  },
  filters: {
  },
  methods: {
    addItem () {
      this.dialog = true
      this.genid()
    },
    editItem (image) {
      this.editedIndex = this.images.indexOf(image)
      this.editedItem = Object.assign({}, image)     
      this.dialog = true
    },
    copyItem (image) {
      this.editedIndex = -1
      this.editedItem = Object.assign({}, image)
      this.dialog = true
      this.genid()
    },
    deleteConfirm (image) {
      this.editedIndex = this.images.indexOf(image)
      this.deleteDialog = true
    },
    deleteItem () {
      if (this.editedIndex > -1) {
        this.images.splice(this.editedIndex, 1);
      }
      const data = JSON.stringify(this.images)
      localStorage.setItem('images', data)
      this.editedIndex = -1
      this.close()
    },
    close () {
      this.dialog = false
      this.deleteDialog = false
      this.importDialog = false
      setTimeout(() => {
        this.editedItem = Object.assign({}, this.defaultItem)
        this.editedIndex = -1
      }, 300)
    },
    save () {
      if (this.editedIndex > -1) {
        //this.updateRoom(this.editedItem)
      } else {
        this.add(this.editedItem)
      }
      this.close()
    },
    _import () {
      var reader = new FileReader()
      reader.onload = (file) => {
        this.images = JSON.parse(file.target.result)
        const data = JSON.stringify(this.images)
        localStorage.setItem('images', data)
      }
      reader.readAsText(this.importFile)
      this.importDialog = false
    },
    _export () {
      const blob = new Blob([JSON.stringify(this.images, null, 2)], {type: 'text/json'})
      const e = document.createEvent('MouseEvents')
      const a = document.createElement('a')
      a.download = this.filename
      a.href = window.URL.createObjectURL(blob)
      a.dataset.downloadurl = ['text/json', a.download, a.href].join(':')
      e.initEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null)
      a.dispatchEvent(e)
    },
    add () {
      this.images.push({
        id: this.editedItem.id,
        kernel: this.editedItem.kernel,
        initrd: this.editedItem.initrd,
        imagefile: this.editedItem.imagefile,
        dtb: this.editedItem.dtb,
        name: this.editedItem.name,
        description: this.editedItem.description,
        type: this.editedItem.type
      })
      const data = JSON.stringify(this.images)
      localStorage.setItem('images', data)
      },
    genid () {
      var id = crypto.createHash('sha1').update(Date.now().toString()).digest('hex')
      var found = this.images.find(function(image) {
        if(image.id == id)
          return true;
      });
      if (!found)
        this.editedItem.id = id
      else 
        this.genid()
    }
  },
  props: {
  },
  mounted () {
  },
  created () {
    this.images = JSON.parse(localStorage.getItem('images')) || []
  },
  computed: {
    formTitle () {
      return this.editedIndex === -1 ? 'New Image' : 'Edit Edit'
    },
  }
}
</script>

<style scoped>

</style>

