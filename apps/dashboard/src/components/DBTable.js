import React, { Component } from "react";
import { Table } from 'antd';
import "antd/dist/antd.css";
import styled from "styled-components";

const Styles = styled.div`
  .table-container {
      top: 30vh;
      background-color: #FAFAFA;
      padding: 0.25%;
  }
`;

export class DBTable extends Component {
    render() {
        return (
            <Styles>
                {/* <SearchBar
                    handleSearchKeyword={this.props.handleSearchKeyword}
                    handleSearchSelect={this.props.handleSearchSelect}
                    handleSearchDates={this.props.handleSearchDates}
                    searchTable={this.props.searchTable}
                    resetTable={this.props.resetTable}>
                </SearchBar> */}
                <Table
                    columns={this.props.columns}
                    pagination={{ showSizeChanger: true }}
                    dataSource={this.props.data}
                    rowKey="id"
                    className="table-container"
                />
            </Styles>
        );
    }
}