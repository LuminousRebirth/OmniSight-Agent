/** 模型库页（T7.12-5 骨架）：模型列表 + 状态徽章（Phase 2 联调审批操作） */
import { useEffect, useState } from "react";
import { Card, Table, Tag } from "antd";
import axios from "axios";

interface ModelItem {
  id: number;
  name: string;
  version: string;
  task_id: number;
  weights_path?: string | null;
  capability_desc?: string | null;
  status: string;
  approved_by?: string | null;
  approved_at?: string | null;
}

const STATUS_COLOR: Record<string, string> = {
  draft: "default", pending: "processing", active: "success", rejected: "error",
};

export default function ModelsPage() {
  const [models, setModels] = useState<ModelItem[]>([]);

  useEffect(() => {
    axios.get<ModelItem[]>("/api/models").then(({ data }) => setModels(data));
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <Card title="模型注册表">
        <Table<ModelItem>
          rowKey="id" size="middle" dataSource={models} pagination={{ pageSize: 8 }}
          columns={[
            { title: "名称", dataIndex: "name", render: (v: string) => <span className="mono">{v}</span> },
            { title: "版本", dataIndex: "version", width: 90 },
            { title: "状态", dataIndex: "status", width: 110,
              render: (s: string) => <Tag color={STATUS_COLOR[s] ?? "default"}>{s}</Tag> },
            { title: "审批人", dataIndex: "approved_by", width: 110, render: (v?: string) => v ?? "—" },
            { title: "能力描述", dataIndex: "capability_desc", ellipsis: true,
              render: (v?: string) => v ?? "—" },
          ]}
        />
      </Card>
    </div>
  );
}
