-- Rivals 고퀄 ESP + Skeleton (적군만 뼈대) + Aimbot + FOV Circle
print("🔫 Rivals ESP + Skeleton (뼈대) 버전 시작...")

local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer
local RunService = game:GetService("RunService")
local Camera = workspace.CurrentCamera
local UserInputService = game:GetService("UserInputService")

local AimbotEnabled = true
local Smoothness = 0.22
local FOV = 130

-- ==================== ESP 설정 ====================
local ESPSettings = {
    Enabled = true,
    TeamCheck = true,           -- 아군은 ESP 안 보임
    Box = true,
    Tracers = true,
    Name = true,
    Distance = true,
    Skeleton = true,            -- 적군만 뼈대 표시
    SkeletonColor = Color3.fromRGB(255, 100, 100),
    BoxColor = Color3.fromRGB(255, 50, 50),
    AllyColor = Color3.fromRGB(80, 180, 255)
}

local ESPObjects = {}
local SkeletonConnections = {}  -- 뼈대 선 저장

-- 뼈대 연결 부위 (인간형 캐릭터 기준)
local skeletonParts = {
    {"Head", "UpperTorso"},
    {"UpperTorso", "LowerTorso"},
    {"UpperTorso", "LeftUpperArm"},
    {"LeftUpperArm", "LeftLowerArm"},
    {"LeftLowerArm", "LeftHand"},
    {"UpperTorso", "RightUpperArm"},
    {"RightUpperArm", "RightLowerArm"},
    {"RightLowerArm", "RightHand"},
    {"LowerTorso", "LeftUpperLeg"},
    {"LeftUpperLeg", "LeftLowerLeg"},
    {"LeftLowerLeg", "LeftFoot"},
    {"LowerTorso", "RightUpperLeg"},
    {"RightUpperLeg", "RightLowerLeg"},
    {"RightLowerLeg", "RightFoot"}
}

local function createESP(player)
    if ESPObjects[player] then return end
    
    local drawings = {}
    drawings.Box = Drawing.new("Square")
    drawings.Box.Thickness = 2
    drawings.Box.Filled = false
    
    drawings.Tracer = Drawing.new("Line")
    drawings.Tracer.Thickness = 1.5
    
    drawings.Name = Drawing.new("Text")
    drawings.Name.Size = 14
    drawings.Name.Center = true
    drawings.Name.Outline = true
    
    drawings.Distance = Drawing.new("Text")
    drawings.Distance.Size = 13
    drawings.Distance.Center = true
    drawings.Distance.Outline = true
    
    ESPObjects[player] = drawings
end

local function updateSkeleton(player, color)
    if not SkeletonConnections[player] then
        SkeletonConnections[player] = {}
    end
    
    local char = player.Character
    if not char then return end
    
    for i, connection in ipairs(skeletonParts) do
        local part1 = char:FindFirstChild(connection[1])
        local part2 = char:FindFirstChild(connection[2])
        
        if part1 and part2 then
            if not SkeletonConnections[player][i] then
                SkeletonConnections[player][i] = Drawing.new("Line")
                SkeletonConnections[player][i].Thickness = 1.5
            end
            
            local pos1 = Camera:WorldToViewportPoint(part1.Position)
            local pos2 = Camera:WorldToViewportPoint(part2.Position)
            
            local line = SkeletonConnections[player][i]
            line.From = Vector2.new(pos1.X, pos1.Y)
            line.To = Vector2.new(pos2.X, pos2.Y)
            line.Color = color
            line.Transparency = 1
            line.Visible = ESPSettings.Skeleton and ESPSettings.Enabled
        end
    end
end

local function updateESP()
    for player, drawings in pairs(ESPObjects) do
        local char = player.Character
        if not char or not char:FindFirstChild("Humanoid") or char.Humanoid.Health <= 0 then
            for _, obj in pairs(drawings) do obj.Visible = false end
            continue
        end

        local isAlly = ESPSettings.TeamCheck and (player.Team == LocalPlayer.Team)
        local color = isAlly and ESPSettings.AllyColor or ESPSettings.BoxColor

        local head = char:FindFirstChild("Head")
        local root = char:FindFirstChild("HumanoidRootPart")
        if not head or not root then continue end

        local headPos = Camera:WorldToViewportPoint(head.Position)
        local rootPos = Camera:WorldToViewportPoint(root.Position)

        if not headPos.Z > 0 then 
            for _, obj in pairs(drawings) do obj.Visible = false end
            continue 
        end

        -- Box ESP
        local top = Camera:WorldToViewportPoint(head.Position + Vector3.new(0, 2.5, 0))
        local bottom = Camera:WorldToViewportPoint(root.Position - Vector3.new(0, 3, 0))
        local height = math.abs(top.Y - bottom.Y)
        local width = height / 2.2

        drawings.Box.Size = Vector2.new(width, height)
        drawings.Box.Position = Vector2.new(top.X - width/2, top.Y)
        drawings.Box.Color = color
        drawings.Box.Visible = ESPSettings.Box and ESPSettings.Enabled

        -- Tracer
        drawings.Tracer.From = Vector2.new(Camera.ViewportSize.X/2, Camera.ViewportSize.Y)
        drawings.Tracer.To = Vector2.new(headPos.X, headPos.Y)
        drawings.Tracer.Color = color
        drawings.Tracer.Visible = ESPSettings.Tracers and ESPSettings.Enabled

        -- Name & Distance
        local distance = math.floor((root.Position - (LocalPlayer.Character and LocalPlayer.Character:FindFirstChild("HumanoidRootPart") and LocalPlayer.Character.HumanoidRootPart.Position or Vector3.new())).Magnitude)

        drawings.Name.Text = player.Name
        drawings.Name.Position = Vector2.new(headPos.X, headPos.Y - 25)
        drawings.Name.Color = color
        drawings.Name.Visible = ESPSettings.Name and ESPSettings.Enabled

        drawings.Distance.Text = distance .. "m"
        drawings.Distance.Position = Vector2.new(headPos.X, headPos.Y + height/2 + 8)
        drawings.Distance.Color = color
        drawings.Distance.Visible = ESPSettings.Distance and ESPSettings.Enabled

        -- Skeleton (적군만)
        if not isAlly then
            updateSkeleton(player, ESPSettings.SkeletonColor)
        else
            -- 아군은 뼈대 안 보이게
            if SkeletonConnections[player] then
                for _, line in pairs(SkeletonConnections[player]) do
                    line.Visible = false
                end
            end
        end
    end
end

-- FOV Circle
local FOVCircle = Drawing.new("Circle")
FOVCircle.Thickness = 2
FOVCircle.NumSides = 100
FOVCircle.Filled = false
FOVCircle.Color = Color3.fromRGB(0, 255, 180)
FOVCircle.Transparency = 0.7
FOVCircle.Visible = true

local function updateFOV()
    FOVCircle.Position = Vector2.new(Camera.ViewportSize.X / 2, Camera.ViewportSize.Y / 2)
    FOVCircle.Radius = FOV
end

-- Aimbot
local function getClosestPlayer()
    local closest = nil
    local shortest = FOV

    for _, player in ipairs(Players:GetPlayers()) do
        if player \~= LocalPlayer and player.Character and player.Character:FindFirstChild("Humanoid") and player.Character.Humanoid.Health > 0 then
            if ESPSettings.TeamCheck and player.Team == LocalPlayer.Team then continue end

            local target = player.Character:FindFirstChild(AimPart) or player.Character:FindFirstChild("HumanoidRootPart")
            if target then
                local screenPos, onScreen = Camera:WorldToViewportPoint(target.Position)
                if onScreen then
                    local dist = (Vector2.new(screenPos.X, screenPos.Y) - Vector2.new(Camera.ViewportSize.X/2, Camera.ViewportSize.Y/2)).Magnitude
                    if dist < shortest then
                        shortest = dist
                        closest = target
                    end
                end
            end
        end
    end
    return closest
end

RunService.RenderStepped:Connect(function()
    updateFOV()
    updateESP()

    if AimbotEnabled then
        local target = getClosestPlayer()
        if target then
            local current = Camera.CFrame
            local targetCF = CFrame.lookAt(current.Position, target.Position)
            Camera.CFrame = current:Lerp(targetCF, Smoothness)
        end
    end
end)

-- 토글 키
UserInputService.InputBegan:Connect(function(input)
    if input.KeyCode == Enum.KeyCode.RightControl then
        AimbotEnabled = not AimbotEnabled
        print("Aimbot: " .. (AimbotEnabled and "ON" or "OFF"))
    elseif input.KeyCode == Enum.KeyCode.RightShift then
        ESPSettings.Enabled = not ESPSettings.Enabled
        print("ESP: " .. (ESPSettings.Enabled and "ON" or "OFF"))
    end
end)

print("✅ ESP + Skeleton 완성!")
print("   적군만 뼈대(Skeleton) 표시")
print("   Right Ctrl = 에임봇 토글")
print("   Right Shift = 전체 ESP 토글")
print("   FOV = " .. FOV .. " (원 크기)")
