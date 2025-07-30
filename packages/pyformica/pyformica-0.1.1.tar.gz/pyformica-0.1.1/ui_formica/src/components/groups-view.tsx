"use client"

import { useState, useEffect } from "react"
import {useNavigate} from "react-router";
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Search, Users } from "lucide-react"
import MainLayout from "./main-layout"
import {getToken} from "@/lib/auth";
import applyCaseMiddleware from "axios-case-converter";
import axios from "axios";

// Define group and user types
interface User {
  id: string
  name: string
  email: string
  role: "admin" | "operator"
}

interface Group {
  groupId: string
  description: string
  members: User[]
}

export default function GroupsView() {
  const router = useNavigate()
  const [groups, setGroups] = useState<Group[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const API_URL = "http://localhost:8000/api"
  const token = getToken()
  const client = applyCaseMiddleware(axios.create())

  // Load groups from localStorage on component mount
  useEffect(() => {
    const fetchGroups = async () => {
      const { data } = await client.get(`${API_URL}/groups`,
      {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      })
      setGroups(data)
      localStorage.setItem("groups", JSON.stringify(data))
    }

    fetchGroups()
  }, [])

  // Filter groups based on search query
  const filteredGroups = groups.filter(
    (group) =>
      group.groupId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      group.description.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">My Groups</h1>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search groups..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredGroups.map((group) => (
            <Card key={group.groupId} className="overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">{group.groupId}</CardTitle>
              </CardHeader>
              <CardContent className="pb-2">
                <p className="text-sm text-muted-foreground mb-4">{group.description}</p>
                <div className="flex items-center gap-1 text-sm">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <span>{group.members.length} members</span>
                </div>
              </CardContent>
              <CardFooter className="flex justify-between items-center pt-2">
                <div className="flex gap-1">
                  {group.members.some((member) => member.role === "admin") && (
                    <Badge variant="outline" className="text-xs">
                      Admin
                    </Badge>
                  )}
                  {group.members.some((member) => member.role === "operator") && (
                    <Badge variant="outline" className="text-xs">
                      Operator
                    </Badge>
                  )}
                </div>
                <Button variant="outline" size="sm" onClick={() => router(`/groups/${group.groupId}`)}>
                  View Details
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>

        {filteredGroups.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No groups found</p>
            {searchQuery && (
              <Button variant="link" onClick={() => setSearchQuery("")} className="mt-2">
                Clear search
              </Button>
            )}
          </div>
        )}
      </div>
    </MainLayout>
  )
}
