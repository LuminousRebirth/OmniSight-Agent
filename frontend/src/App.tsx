import { useState } from "react";
import {
  BrowserRouter, NavLink, Route, Routes, useLocation,
} from "react-router-dom";
import { Card, Layout, Menu, Typography } from "antd";
import {
  DatabaseOutlined, MenuFoldOutlined, MenuUnfoldOutlined, MessageOutlined,
  RobotOutlined, ScanOutlined, SettingOutlined,
} from "@ant-design/icons";
import KnowledgePage from "./pages/KnowledgePage";

const { Header, Sider, Content } = Layout;

/** 页面定义：Chat / 识别工作台 / Agent / 系统设置(3子页) / 知识库 */
type Page = { path: string; label: string; desc: string };

const CHAT: Page = { path: "/chat", label: "Chat 对话", desc: "Agent 对话与推理轨迹" };
const DETECT: Page = { path: "/detect", label: "识别工作台", desc: "图片 / 视频 / 实时检测" };
const AGENT: Page = { path: "/agent-builder", label: "Agent 智能体", desc: "可视化编排与多 Agent 协作" };
const SETTINGS: Page[] = [
  { path: "/datasets", label: "数据集", desc: "数据管理与标注" },
  { path: "/models", label: "模型库", desc: "模型审批与注册表" },
  { path: "/training", label: "训练中心", desc: "训练任务与指标" },
];
const KNOWLEDGE: Page = { path: "/knowledge", label: "知识库", desc: "RAG 知识管理与检索" };

function Placeholder({ label, desc }: Page) {
  return (
    <Card style={{ margin: 24, borderRadius: 8 }}>
      <Typography.Title level={3} style={{ marginTop: 0 }}>{label}</Typography.Title>
      <Typography.Paragraph type="secondary">{desc}</Typography.Paragraph>
      <Typography.Text type="secondary">页面骨架已就绪，功能随构建阶段接入</Typography.Text>
    </Card>
  );
}

function Shell({ collapsed, onCollapse }: { collapsed: boolean; onCollapse: (v: boolean) => void }) {
  const { pathname } = useLocation();

  const menuItems = [
    { key: CHAT.path, icon: <MessageOutlined />, label: <NavLink to={CHAT.path}>{CHAT.label}</NavLink> },
    { key: DETECT.path, icon: <ScanOutlined />, label: <NavLink to={DETECT.path}>{DETECT.label}</NavLink> },
    { key: AGENT.path, icon: <RobotOutlined />, label: <NavLink to={AGENT.path}>{AGENT.label}</NavLink> },
    { key: KNOWLEDGE.path, icon: <DatabaseOutlined />, label: <NavLink to={KNOWLEDGE.path}>{KNOWLEDGE.label}</NavLink> },
    {
      key: "settings", icon: <SettingOutlined />, label: "系统设置",
      children: SETTINGS.map((p) => ({ key: p.path, label: <NavLink to={p.path}>{p.label}</NavLink> })),
    },
  ];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        collapsible collapsed={collapsed} onCollapse={onCollapse} trigger={null}
        width={220} theme="light"
        style={{ borderRight: "1px solid var(--border)" }}
      >
        {/* 顶部：标题 + 折叠按钮 */}
        <div style={{
          height: 56, display: "flex", alignItems: "center",
          justifyContent: collapsed ? "center" : "space-between",
          paddingInline: collapsed ? 0 : 16, gap: 8,
        }}>
          {!collapsed && (
            <span style={{ fontWeight: 600, color: "var(--primary)", whiteSpace: "nowrap" }}>
              OmniSight-Agent
            </span>
          )}
          <button
            type="button"
            aria-label={collapsed ? "展开侧边栏" : "收起侧边栏"}
            onClick={() => onCollapse(!collapsed)}
            style={{
              width: 28, height: 28, borderRadius: 8, border: "none", cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center",
              background: "var(--primary-soft)", color: "var(--primary)", fontSize: 14, padding: 0,
            }}
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </button>
        </div>
        <Menu mode="inline" items={menuItems} selectedKeys={[pathname]} style={{ borderInlineEnd: "none" }} />
      </Sider>
      <Layout>
        <Header style={{
          background: "#fff", borderBottom: "1px solid var(--border)",
          display: "flex", alignItems: "center", paddingInline: 24,
        }}>
          <Typography.Title level={4} style={{ margin: 0, color: "var(--text)" }}>
            OmniSight-Agent 识别检测工作台
          </Typography.Title>
        </Header>
        <Content style={{ background: "var(--bg)" }}>
          <Routes>
            <Route path={CHAT.path} element={<Placeholder {...CHAT} />} />
            <Route path={DETECT.path} element={<Placeholder {...DETECT} />} />
            <Route path={AGENT.path} element={<Placeholder {...AGENT} />} />
            {SETTINGS.map((p) => (
              <Route key={p.path} path={p.path} element={<Placeholder {...p} />} />
            ))}
            <Route path={KNOWLEDGE.path} element={<KnowledgePage />} />
            <Route path="*" element={<Placeholder {...DETECT} />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default function App() {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <BrowserRouter>
      <Shell collapsed={collapsed} onCollapse={setCollapsed} />
    </BrowserRouter>
  );
}
