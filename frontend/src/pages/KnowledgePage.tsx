import { useEffect, useRef } from "react";
import { Button, Card, Col, Row, Statistic, Table, Upload } from "antd";
import { CloudUploadOutlined, InboxOutlined } from "@ant-design/icons";
import * as echarts from "echarts";

/** 知识库（RAG 核心）——骨架：多文件上传 / 索引 / 可视化统计。
 *  Phase 2 接真实 RAG API（/api/rag/*），当前为静态示例数据占位。 */
const DOC_TYPE_STATS = [
  { name: "规范文档", value: 12 },
  { name: "历史案例", value: 45 },
  { name: "告警预案", value: 8 },
  { name: "模型档案", value: 3 },
];

const DOCS = [
  { key: "1", title: "GB 安全帽使用规范", doc_type: "规范文档", chunks: 23, status: "已索引" },
  { key: "2", title: "轮毂质检历史案例集", doc_type: "历史案例", chunks: 156, status: "已索引" },
  { key: "3", title: "烟火告警处置预案", doc_type: "告警预案", chunks: 18, status: "已索引" },
  { key: "4", title: "helmet_v26 模型档案", doc_type: "模型档案", chunks: 5, status: "已索引" },
];

const COLUMNS = [
  { title: "文档标题", dataIndex: "title" },
  { title: "类型", dataIndex: "doc_type", width: 110 },
  { title: "分块数", dataIndex: "chunks", width: 90 },
  { title: "状态", dataIndex: "status", width: 90 },
];

export default function KnowledgePage() {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current) return;
    const chart = echarts.init(chartRef.current);
    chart.setOption({
      tooltip: { trigger: "item" },
      legend: { bottom: 0 },
      series: [{
        type: "pie",
        radius: ["42%", "70%"],
        itemStyle: { borderRadius: 6, borderColor: "#fff", borderWidth: 2 },
        label: { formatter: "{b}: {c}" },
        data: DOC_TYPE_STATS,
        color: ["#2563EB", "#60A5FA", "#93C5FD", "#BFDBFE"],
      }],
    });
    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);
    return () => { window.removeEventListener("resize", onResize); chart.dispose(); };
  }, []);

  return (
    <div style={{ padding: 24 }}>
      {/* 统计卡片 */}
      <Row gutter={16}>
        <Col span={6}><Card><Statistic title="文档总数" value={68} /></Card></Col>
        <Col span={6}><Card><Statistic title="知识分块" value={1204} /></Card></Col>
        <Col span={6}><Card><Statistic title="已索引" value={68} /></Card></Col>
        <Col span={6}><Card><Statistic title="向量维度" value={1024} /></Card></Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 16 }}>
        {/* 可视化：文档类型分布 */}
        <Col span={10}>
          <Card title="文档类型分布" style={{ height: 380 }}>
            <div ref={chartRef} style={{ height: 300 }} />
          </Card>
        </Col>
        {/* 多文件上传 / 索引 */}
        <Col span={14}>
          <Card title="多文件上传 / 索引">
            <Upload.Dragger multiple>
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p className="ant-upload-text">点击或拖拽文件到此处上传</p>
              <p className="ant-upload-hint">支持 PDF / Word / Markdown / 图片，自动分块 + 向量化索引（Milvus）</p>
            </Upload.Dragger>
            <Button type="primary" icon={<CloudUploadOutlined />} style={{ marginTop: 12 }}>
              开始索引
            </Button>
          </Card>
        </Col>
      </Row>

      {/* 文档列表 */}
      <Card title="知识文档列表" style={{ marginTop: 16 }}>
        <Table dataSource={DOCS} columns={COLUMNS} pagination={{ pageSize: 5 }} size="middle" />
      </Card>
    </div>
  );
}
