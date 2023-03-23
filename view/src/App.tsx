import './App.scss'
import TableView from './components/TableView'
import EditView from './components/EditView'
import { useState } from 'react'

// ? This interface/object template/class - defines the JSON structure of the displayed table/relation for this application
export interface RelationView {
  columns: Array<string>
  rows: Array<{ [key: string]: any }> // ? represents the string-key, arbitrary-value type, for example [{"id": 2, "name": "mehdi"}, {"id": 1, "name": "fuad"}]}
}

// ? In React, a function returning HTML script is called a component, 
// ? and App is our main component, hosting the table editing menu and table view
function App() {

  // ? state (currentRelationView) - is the JS/TS object holding the dynamic values
  // ? setState (setCurrentRelationView) - is the JS/TS method used to update the state object
  // ? our state `currentRelationView` holds the necessary data to display the requested table/relation
  // ? Note the generic type we defined above - type strict will help you keep the track by its strict types
  const [currentRelationView, setCurrentRelationView] = useState<RelationView>({
    columns: [],
    rows: []
  })

  return (
    // ? The main block containing all the editible DOM elements
    <div className="App">
      <div id="main-view">
        {/* Below component is the user edit menu to create/modify the required table. Refer to `handleRelationViewUpdate` to learn about props*/}
        <EditView relationView={currentRelationView} onRelationChange={handleRelationViewUpdate} />
        {/* TableView component is just for displaying the table on the right side of the view */}
        <TableView relationView={currentRelationView} />
        <TableView relationView={currentRelationView} />
      </div>
    </div>
  )

  // ? A props funcion for the EditView - keeping the relation view for up-to-date to be displayed on the right side of the window
  function handleRelationViewUpdate(relationView: RelationView) {
    // ? Here a few data type handling is done in order to properly diplay the BOOLEAN types since HTML visualizes true and false types as blank
    // ? First loop iterates through the displayed rows
    for (let i = 0; i < relationView.rows.length; i++) {
      // ? The second loop checks each field type
      for (let fieldKey of Object.keys(relationView.rows[i])) {
        let fieldValue = relationView.rows[i][fieldKey]
        // ? And it stringifies it if it is boolean
        if (typeof (fieldValue) === 'boolean') {
          relationView.rows[i][fieldKey] = fieldValue.toString()
        }
      }
    }
    //? Sorting by ID for better sequential visualization
    relationView.rows = relationView.rows.sort((a, b) => a.id - b.id)
    // ? Funcionality of RelationView explained on the line it's defined
    setCurrentRelationView(relationView)
  }
}

export default App
