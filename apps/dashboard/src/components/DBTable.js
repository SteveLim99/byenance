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