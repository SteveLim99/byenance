import './App.css';
import React, { Component } from 'react';
import CloudDownloadIcon from '@material-ui/icons/CloudDownload';
import { CircularProgress, Button } from '@material-ui/core';
import axios from "axios";

import { DBTable } from "./components/DBTable";

class App extends Component {
  constructor() {
    super();

    const entries_col = [
      {
        title: "Entry ID",
        dataIndex: "id",
        sorter: (a, b) => a.id - b.id,
        ellipsis: true,
        sortDirections: ["descend", "ascend"]
      },
      {
        title: "Unit",
        dataIndex: "unit",
        sorter: (a, b) => a.unit.localeCompare(b.unit),
        ellipsis: true,
        sortDirections: ["descend", "ascend"]
      },
      {
        title: "Datetime",
        dataIndex: "datetime",
        sorter: (a, b) => new Date(a.datetime) - new Date(b.datetime),
        ellipsis: true,
        sortDirections: ["descend", "ascend"]
      },
      {
        title: "Opening Price",
        dataIndex: "opening",
        sorter: (a, b) => a.opening - b.opening,
        ellipsis: true,
        sortDirections: ["descend", "ascend"]
      },
      {
        title: "Closing Price",
        dataIndex: "closing",
        sorter: (a, b) => a.closing - b.closing,
        ellipsis: true,
        sortDirections: ["descend", "ascend"]
      },
      {
        title: "Interpolated",
        dataIndex: "interpolated",
        sorter: (a, b) => a.interpolated.length - b.interpolated.length,
        ellipsis: true,
        sortDirections: ["descend", "ascend"]
      }
    ];

    const returns_col = [
      {
        title: "Return ID",
        dataIndex: "id",
        sorter: (a, b) => a.id - b.id,
        ellipsis: true,
        sortDirections: ["descend", "ascend"]
      },
      {
        title: "Unit",
        dataIndex: "unit",
        sorter: (a, b) => a.unit.localeCompare(b.unit),
        ellipsis: true,
        sortDirections: ["descend", "ascend"]
      },
      {
        title: "Datetime",
        dataIndex: "date",
        sorter: (a, b) => new Date(a.date) - new Date(b.date),
        ellipsis: true,
        sortDirections: ["descend", "ascend"]
      },
      {
        title: "Return based on Opening Prices",
        dataIndex: "opening",
        sorter: (a, b) => a.opening - b.opening,
        ellipsis: true,
        sortDirections: ["descend", "ascend"]
      },
      {
        title: "Return based on Closing Prices",
        dataIndex: "closing",
        sorter: (a, b) => a.closing - b.closing,
        ellipsis: true,
        sortDirections: ["descend", "ascend"]
      }
    ];

    this.state = {
      view: true,
      startTitle: "Click Start to Fetch Database Results",
      entries_col: entries_col,
      returns_col: returns_col,
      entries_data: null,
      returns_data: null
    }
  }

  handleGetStarted = async (e) => {
    e.preventDefault()
    const loader = document.getElementById("loading");
    const start_button = document.getElementById("start-button");

    loader.style.display = "flex";
    start_button.style.display = 'none';

    const entries_endpoint = "/api/getEntries"
    const returns_endpoint = "/api/getRollingReturns"
    this.setState({
      startTitle: "Setting up the Database. This may take awhile..."
    })

    try {
      const entries_response = await axios.get(entries_endpoint)
      this.setState({
        startTitle: "Set up complete! Fetching results from database..."
      })
      const returns_response = await axios.get(returns_endpoint)

      if (entries_response.data['status'] === 'success' && returns_response.data['status'] === 'success') {
        const entries_data_source = entries_response.data["entries"]
        const returns_data_source = returns_response.data["returns"]

        this.setState({
          entries_data: entries_data_source,
          returns_data: returns_data_source,
          view: false
        })
      } else {
        alert("An error occured when fetching data from the database. Please try again.")
      }
    } catch (error) {
      console.log(error)
      alert("An error occurred when fetching data from the database.")
    } finally {
      this.setState({
        startTitle: "Click Start to Fetch Database Results"
      })
      loader.style.display = "none";
      start_button.style.display = 'flex';
    }
  }

  render() {
    if (this.state.view === true) {
      return (
        <div className="App">
          <header className="App-header">
            <h2 style={{ fontFamily: 'monospace', color: 'white' }}>
              {this.state.startTitle}
            </h2>
            <CircularProgress
              color='primary'
              className='progress-bar'
              id='loading'
              style={{ display: 'none' }}>
            </CircularProgress >
            <Button
              type="submit"
              variant="outlined"
              color="primary"
              size="large"
              id="start-button"
              startIcon={<CloudDownloadIcon />}
              onClick={(e) => { this.handleGetStarted(e) }}
            >
              Start
            </Button>
          </header>
        </div >
      );
    } else {
      return (
        <div>
          <div className="App">
            <header className="App-header">
              <div className="containers">
                <h3 className="containers_headers">
                  Hourly Binance Entries
                </h3>
                <DBTable
                  columns={this.state.entries_col}
                  data={this.state.entries_data}
                />
              </div>
              <div className="containers">
                <h3 className="containers_headers">
                  Daily Returns
                </h3>
                <DBTable
                  columns={this.state.returns_col}
                  data={this.state.returns_data}
                />
              </div>
            </header>
          </div>
        </div >
      );
    }
  }
}

export default App;