-- 文件系统表：支持文件夹和文件的树形结构
-- 用户隔离：每个用户有独立的文件空间

-- 文件夹表
CREATE TABLE IF NOT EXISTS t_folder (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES t_user(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES t_folder(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    path TEXT NOT NULL,  -- 完整路径，如 /root/folder1/subfolder
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, parent_id, name),  -- 同一父文件夹下不能有重名
    CHECK (name != '' AND name NOT LIKE '%/%')  -- 文件夹名不能包含斜杠
);

-- 文件表
CREATE TABLE IF NOT EXISTS t_file (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES t_user(id) ON DELETE CASCADE,
    folder_id INTEGER REFERENCES t_folder(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,  -- 原始文件名
    file_size BIGINT NOT NULL DEFAULT 0,
    mime_type VARCHAR(100),
    storage_path TEXT NOT NULL,  -- 存储路径：users/{user_id}/files/{uuid}
    file_hash VARCHAR(64),  -- SHA256哈希，用于去重
    metadata JSONB,  -- 额外元数据（如图片尺寸、文档页数等）
    tags TEXT[],  -- 标签数组
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, folder_id, filename)  -- 同一文件夹下不能有重名文件
);

-- 创建索引
CREATE INDEX idx_folder_user_id ON t_folder(user_id);
CREATE INDEX idx_folder_parent_id ON t_folder(parent_id);
CREATE INDEX idx_folder_path ON t_folder(path);
CREATE INDEX idx_file_user_id ON t_file(user_id);
CREATE INDEX idx_file_folder_id ON t_file(folder_id);
CREATE INDEX idx_file_hash ON t_file(file_hash);
CREATE INDEX idx_file_tags ON t_file USING GIN(tags);

-- 为每个用户创建根文件夹的触发器
CREATE OR REPLACE FUNCTION create_user_root_folder()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO t_folder (user_id, parent_id, name, path, description)
    VALUES (NEW.id, NULL, 'root', '/root', '用户根目录');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_user_root_folder
AFTER INSERT ON t_user
FOR EACH ROW
EXECUTE FUNCTION create_user_root_folder();

-- 为现有用户创建根文件夹
INSERT INTO t_folder (user_id, parent_id, name, path, description)
SELECT id, NULL, 'root', '/root', '用户根目录'
FROM t_user
WHERE id NOT IN (SELECT user_id FROM t_folder WHERE parent_id IS NULL)
ON CONFLICT DO NOTHING;
