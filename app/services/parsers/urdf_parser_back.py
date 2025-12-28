import xml.etree.ElementTree as ET
from typing import Dict, Any, List

class URDFParser_back:
    def parse_urdf(self, xml_str: str, robot_name: str) -> List[Dict[str, Any]]:
        """
        解析URDF/Xacro文件
        """
        chunks = []
        
        try:
            root = ET.fromstring(xml_str)
            
            # 解析joints
            for joint in root.findall("joint"):
                name = joint.attrib.get("name")
                jtype = joint.attrib.get("type")
                limit = joint.find("limit")
                
                if name and jtype:
                    text = f"Joint {name} is a {jtype} joint."
                    if limit is not None:
                        text += (
                            f" Limits: lower={limit.attrib.get('lower')}, "
                            f"upper={limit.attrib.get('upper')}."
                        )
                    
                    metadata = {
                        "category": "urdf_joint",
                        "robot": robot_name,
                        "joint": name,
                    }
                    
                    chunks.append({"text": text, "metadata": metadata})
            
            # 解析links
            for link in root.findall("link"):
                name = link.attrib.get("name")
                if name:
                    text = f"Link {name} is part of the robot structure."
                    metadata = {
                        "category": "urdf_link",
                        "robot": robot_name,
                        "link": name,
                    }
                    chunks.append({"text": text, "metadata": metadata})
                    
        except ET.ParseError as e:
            print(f"Invalid XML format: {e}")
        
        return chunks