"use client"

import { useState, useEffect } from "react"
import {useNavigate} from "react-router";
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ArrowLeft } from "lucide-react"
import MainLayout from "./main-layout"
import axios from "axios";
import applyCaseMiddleware from "axios-case-converter";
import {getToken} from "@/lib/auth";

// Define group and user types
interface User {
  id: string
  name: string
  email: string
  role: "admin" | "operator"
  isSuperuser: boolean
}

interface Group {
  groupId: string
  description: string
  members: string[]
}

interface GroupDetailViewProps {
  groupId: string
}

export default function GroupDetailView({ groupId }: GroupDetailViewProps) {
  const router = useNavigate()
  const [group, setGroup] = useState<Group | null>(null)
  const [members, setMembers] = useState<User[]>([])
  const API_URL = "http://localhost:8000/api"
  const token = getToken()
  const client = applyCaseMiddleware(axios.create())

  // Load group data
  useEffect(() => {
    const loadGroup = () => {
      try {
        const fetchData = async () => {
          const { data: group } = await client.get(`${API_URL}/groups/${groupId}`,
            {
              headers: {
                "Authorization": `Bearer ${token}`,
              },
            })
          setGroup(group)
          const { data: members } = await client.get(`${API_URL}/groups/${groupId}/members`,
          {
            headers: {
              "Authorization": `Bearer ${token}`,
            },
          })
          setMembers(members)
        }
        fetchData()
      } catch (error) {
        console.error("Error loading group:", error)
        router("/groups")
      }
    }

    loadGroup()
  }, [groupId, router, token, client])

  if (!group) {
    return (
      <MainLayout>
        <div className="container mx-auto py-6">
          <p>Loading group details...</p>
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router("/groups")}>
            <ArrowLeft className="h-5 w-5" />
            <span className="sr-only">Back to groups</span>
          </Button>
          <div className="flex-1">
            <div>
              <h1 className="text-2xl font-bold">{group.groupId}</h1>
              <p className="text-muted-foreground">{group.description}</p>
            </div>
          </div>
        </div>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">Members ({group.members.length})</h2>
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.map((member) => (
                  <TableRow key={member.id}>
                    <TableCell className="font-medium">{member.name}</TableCell>
                    <TableCell>{member.email}</TableCell>
                    <TableCell>
                      <Badge variant={member.role === "admin" || member.isSuperuser ? "default" : "outline"}>
                        {member.isSuperuser ? "Superuser" : (member.role === "admin" ? "Administrator" : "Operator")}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
