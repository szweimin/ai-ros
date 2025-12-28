import xml.etree.ElementTree as ET
from typing import Dict, Any, List

class URDFParser:
    def parse_urdf(self, xml_str: str, robot_name: str) -> List[Dict[str, Any]]:
        """
        增强版URDF解析器 - 提取详细信息
        """
        chunks = []
        
        try:
            root = ET.fromstring(xml_str)
            robot_name_attr = root.attrib.get("name", robot_name)
            
            # 1. 机器人概述
            chunks.append({
                "text": f"Robot '{robot_name_attr}' URDF description. This is a robotic system defined in URDF format.",
                "metadata": {
                    "category": "urdf_overview",
                    "robot": robot_name_attr,
                    "element_type": "robot"
                }
            })
            
            # 2. 详细解析每个链接
            links = root.findall("link")
            for link in links:
                name = link.attrib.get("name")
                if not name:
                    continue
                
                description_parts = [f"Link '{name}' in robot '{robot_name_attr}':"]
                
                # 检查视觉元素
                visual = link.find("visual")
                if visual is not None:
                    geometry = visual.find("geometry")
                    if geometry is not None:
                        for geom_type in ['box', 'cylinder', 'sphere', 'mesh']:
                            geom = geometry.find(geom_type)
                            if geom is not None:
                                if geom_type == 'box':
                                    size = geom.attrib.get("size", "unknown")
                                    description_parts.append(f"Visual geometry is a BOX with size {size}.")
                                elif geom_type == 'cylinder':
                                    length = geom.attrib.get("length", "unknown")
                                    radius = geom.attrib.get("radius", "unknown")
                                    description_parts.append(f"Visual geometry is a CYLINDER with length {length} and radius {radius}. This looks like a WHEEL.")
                                elif geom_type == 'sphere':
                                    radius = geom.attrib.get("radius", "unknown")
                                    description_parts.append(f"Visual geometry is a SPHERE with radius {radius}.")
                                break
                
                # 检查惯性
                inertial = link.find("inertial")
                if inertial is not None:
                    mass_elem = inertial.find("mass")
                    if mass_elem is not None:
                        mass = mass_elem.attrib.get("value", "unknown")
                        description_parts.append(f"Mass: {mass}.")
                
                text = " ".join(description_parts)
                
                # 如果是轮子，添加额外标签
                if 'wheel' in name.lower():
                    text += " This is a WHEEL component."
                
                chunks.append({
                    "text": text,
                    "metadata": {
                        "category": "urdf_link",
                        "robot": robot_name_attr,
                        "link": name,
                        "is_wheel": 'wheel' in name.lower(),
                        "element_type": "link"
                    }
                })
            
            # 3. 详细解析每个关节
            joints = root.findall("joint")
            for joint in joints:
                name = joint.attrib.get("name")
                jtype = joint.attrib.get("type", "unknown")
                
                if not name:
                    continue
                
                description_parts = [f"Joint '{name}' is a {jtype.upper()} joint."]
                
                # 连接关系
                parent = joint.find("parent")
                child = joint.find("child")
                
                if parent is not None:
                    parent_link = parent.attrib.get("link", "unknown")
                    description_parts.append(f"Parent link: '{parent_link}'.")
                
                if child is not None:
                    child_link = child.attrib.get("link", "unknown")
                    description_parts.append(f"Child link: '{child_link}'.")
                
                # 如果是轮子关节，特别说明
                if 'wheel' in name.lower():
                    description_parts.append("This joint connects a WHEEL to the robot.")
                
                # 限制
                limit = joint.find("limit")
                if limit is not None:
                    effort = limit.attrib.get("effort", "unlimited")
                    velocity = limit.attrib.get("velocity", "unlimited")
                    description_parts.append(f"Joint limits: effort={effort}, velocity={velocity}.")
                
                text = " ".join(description_parts)
                
                chunks.append({
                    "text": text,
                    "metadata": {
                        "category": "urdf_joint",
                        "robot": robot_name_attr,
                        "joint": name,
                        "joint_type": jtype,
                        "is_wheel_joint": 'wheel' in name.lower(),
                        "element_type": "joint"
                    }
                })
            
            # 4. 添加机器人总结
            if links and joints:
                link_names = [link.attrib.get("name") for link in links if link.attrib.get("name")]
                joint_names = [joint.attrib.get("name") for joint in joints if joint.attrib.get("name")]
                
                wheel_links = [name for name in link_names if 'wheel' in name.lower()]
                wheel_joints = [name for name in joint_names if 'wheel' in name.lower()]
                
                summary = f"Robot '{robot_name_attr}' summary: "
                summary += f"{len(links)} links ({', '.join(link_names)}), "
                summary += f"{len(joints)} joints ({', '.join(joint_names)}). "
                summary += f"It has {len(wheel_links)} wheels: {', '.join(wheel_links)}."
                
                chunks.append({
                    "text": summary,
                    "metadata": {
                        "category": "urdf_summary",
                        "robot": robot_name_attr,
                        "link_count": len(links),
                        "joint_count": len(joints),
                        "wheel_count": len(wheel_links),
                        "element_type": "summary"
                    }
                })
            
        except Exception as e:
            print(f"Error parsing URDF: {e}")
            chunks.append({
                "text": f"URDF for {robot_name}: {xml_str[:200]}...",
                "metadata": {"category": "urdf_raw", "robot": robot_name}
            })
        
        return chunks